# -*- coding: utf-8 -*-

from xml.dom import minidom
from xml.dom.minidom import parse, parseString

from datetime import date, datetime
from pytz import timezone
import json, base64, re
import collections, requests
import logging

import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.exceptions import UserError, RedirectWarning, ValidationError

_logger = logging.getLogger(__name__)

__check_cfdi_re = re.compile(u'''([A-Z]|[a-z]|[0-9]| |Ñ|ñ|!|"|%|&|'|´|-|:|;|>|=|<|@|_|,|\{|\}|`|~|á|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü)''')

def get_string_cfdi(text, size=100):
    if not text:
        return None
    for char in __check_cfdi_re.sub('', text):
        text = text.replace(char, ' ')
    return text.strip()[:size]

def create_list_html(array):
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'



class AltaCatalogosCFDI(models.TransientModel):
    _inherit = 'cf.mx.alta.catalogos.wizard'

    @api.multi
    def getElectronicPayment(self):
        MoveLine = self.env['account.move.line']
        line_ids = MoveLine.sudo().search([('cadena_sat', '!=', False)])
        for line in line_ids:
            line.sudo().getElectronicPayment()
        return True



class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        res = super(AccountInvoice, self.with_context(invoice_id=self.id, payment_id=credit_aml.payment_id)).assign_outstanding_credit(credit_aml_id)
        return res

    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountInvoice, self).register_payment(payment_line, writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        if self.env.context.get('invoice_id') and self.env.context.get('payment_id'):
            payment_id = self.env.context["payment_id"]
            if payment_id.filtered(lambda r: r.cfdi_is_required()):
                payment_id.action_validate_cfdi()
        return res

    @api.one
    @api.depends('payment_move_line_ids.amount_residual')
    def _get_payment_info_JSON(self):
        res = super(AccountInvoice, self)._get_payment_info_JSON()
        if self.payments_widget != "false":
            MoveLine = self.env['account.move.line']
            payments_widget = json.loads(self.payments_widget)
            for vals in payments_widget.get("content", []):
                line_id = MoveLine.browse([vals.get("payment_id")])
                if line_id and line_id.payment_id:
                    vals['account_payment_id'] = line_id.payment_id.id
                    vals['cfdi_timbre_id'] = line_id.payment_id and line_id.payment_id.cfdi_timbre_id and line_id.payment_id.cfdi_timbre_id.id or None
            self.payments_widget = json.dumps(payments_widget)
        return res





class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"
    _description = "Register payments on multiple invoices"

    hide_formapago_id = fields.Boolean(compute='_compute_hide_formapago_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')
    formapago_code = fields.Char(related='formapago_id.clave')
    spei_tipo_cadenapago = fields.Selection([
            ('01', 'SPEI')
        ], string="Tipo de Cadena de Pago", domain=[('formapago_id.clave', '!=', '03')],
        help="Se debe registrar la clave del tipo de cadena de pago que genera la entidad receptora del pago.", default="")
    spei_certpago = fields.Text(string="Certificado Pago SPEI")
    spei_cadpago = fields.Text(string="Cadena Pago SPEI")
    spei_sellopago = fields.Text(string="Sello Pago SPEI")


    @api.one
    @api.depends('journal_id')
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids:
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True

    def get_payment_vals(self):
        rec = super(AccountRegisterPayments, self).get_payment_vals()
        vals = {
            'formapago_id': self.formapago_id and self.formapago_id.id or None
        }
        rec.update(vals)
        return rec

class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["mail.thread", "account.payment"]

    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    def _compute_date_invoice_cfdi(self):
        _logger.info("self.payment_date 000 - %s "%self.payment_date)
        if self.date_invoice_cfdi:
            return
        tz = self.env.user.tz or "America/Mexico_City"

        hora_factura_utc = datetime.now(timezone("UTC"))
        dtz = hora_factura_utc.astimezone(timezone(tz)).strftime("%Y-%m-%d %H:%M:%S")
        dtz = dtz.replace(" ", "T")
        _logger.info("self.payment_date 001 - %s"%dtz)
        self.date_invoice_cfdi = dtz

    hide_formapago_id = fields.Boolean(compute='_compute_hide_formapago_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    
    date_invoice_cfdi = fields.Char(string="Invoice Date", copy=False, store=True, compute='_compute_date_invoice_cfdi')
    
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')
    formapago_code = fields.Char(related='formapago_id.clave')
    spei_tipo_cadenapago = fields.Selection([
            ('01', 'SPEI')
        ], string="Tipo de Cadena de Pago", domain=[('formapago_id.clave', '!=', '03')],
        help="Se debe registrar la clave del tipo de cadena de pago que genera la entidad receptora del pago.", default="")
    spei_certpago = fields.Text(string="Certificado Pago SPEI")
    spei_cadpago = fields.Text(string="Cadena Pago SPEI")
    spei_sellopago = fields.Text(string="Sello Pago SPEI")

    cfdi_timbre_id = fields.Many2one('cfdi.timbres.sat', string=u'Timbre SAT')

    
    @api.one
    @api.depends('journal_id')
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids:
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        for record in self.filtered(lambda r: r.cfdi_is_required()):
            record.action_validate_cfdi()
        return res

    @api.multi
    def cfdi_is_required(self):
        self.ensure_one()
        required = (
            self.partner_type == "customer" and 
            self.payment_type == 'inbound' and
            self.invoice_ids.filtered(lambda i: i.type == 'out_invoice') and 
            self.journal_id.id in self.env.user.company_id.cfd_mx_journal_ids.ids
        )
        if not required:
            return required
        if not self.invoice_ids:
            raise UserError(_(
                'Is necessary assign the invoices that are paid with this '
                'payment to allow relate in the CFDI the fiscal '
                'documents that are affected with this record.'))
        if False in self.invoice_ids.mapped('uuid'):
            raise UserError(_(
                'Some of the invoices that will be paid with this record '
                'is not signed, and the UUID is required to indicate '
                'the invoices that are paid with this CFDI'))

        codigo_postal_id = self.journal_id and self.journal_id.codigo_postal_id or False
        regimen_id = self.company_id.partner_id.regimen_id or False
        tz = self.env.user.tz or False
        if not codigo_postal_id:
            raise UserError(_('No se definio Lugar de Exception (C.P.)'))
        if not regimen_id: 
            raise UserError(_('No se definio Regimen Fiscal para la Empresa'))
        if not tz:
            raise UserError(_('El usuario no tiene definido Zona Horaria'))
        if not self.partner_id.vat:
            raise UserError(_('No se especifico el RFC para el Cliente'))
        if not self.company_id.partner_id.vat:
            raise UserError(_('No se especifico el RFC para la Empresa'))
        if self.partner_id.es_extranjero:
            if not (self.partner_id.country_id and self.partner_id.country_id.code_alpha3 or False):
                raise UserError(_('No se especifico el codigo del Pais'))
        return required


    @api.multi
    def action_validate_cfdi(self):
        for rec in self:
            res = rec.create_cfdi_payment()
            if res.get('message'):
                message = res['message']
                rec.message_post(body=message)
                raise UserError(message)
            else:
                self.get_process_data(res.get('result'))
        return True

    @api.multi
    def create_cfdi_payment(self):
        self.ensure_one()
        cfdi = collections.OrderedDict()
        cfdi["cfdi:Comprobante"] = self.cfdi_payment_comprobante()
        if self.cfdi_timbre_id:
            cfdi["cfdi:Comprobante"]["cfdi:CfdiRelacionados"] = self.cfdi_payment_relacionados()
        cfdi["cfdi:Comprobante"]["cfdi:Emisor"] = self.cfdi_payment_emisor()
        cfdi["cfdi:Comprobante"]["cfdi:Receptor"] = self.cfdi_payment_receptor()
        cfdi["cfdi:Comprobante"]["cfdi:Conceptos"] = self.cfdi_payment_conceptos()
        cfdi["cfdi:Comprobante"]["cfdi:Complemento"] = self.cfdi_payment_complemento()
        ordered_list = [{key: val} for key, val in cfdi.items()]
        cfdi_json = json.dumps(ordered_list)
        url = "%s/cfdi/stamp/%s/%s"%(self.company_id.cfd_mx_host, self.company_id.cfd_mx_db, self.company_id.vat)
        headers = {'Content-Type': 'application/json'}
        data = {
            "params": {
                "test": self.company_id.cfd_mx_test,
                "pac": self.company_id.cfd_mx_pac,
                "version": self.company_id.cfd_mx_version,
                "cfdi": cfdi_json
            }
        }
        data_json = json.dumps(data)
        _logger.info(data)
        res = requests.post(url=url, data=data_json, headers=headers)
        res_datas = res.json()
        msg = res_datas.get('error') and res_datas['error'].get('data') and res_datas['error']['data'].get('message')
        if msg:
            return res_datas['error']['data']
        if res_datas.get('error'):
            return res_datas['error']
        if res_datas.get('result') and res_datas['result'].get('error'):
            return res_datas['result']['error']
        return res_datas

    def get_process_data(self, res):
        context = dict(self._context) or {}
        fname = "cfd_%s.xml"%(self.name or '')
        if context.get('type') and context.get('type') == 'pagos':
            fname = '%s.xml'%(res.get('UUID') or res.get('uuid') or self.name or '')
        Currency = self.env['res.currency']
        attachment_obj = self.env['ir.attachment']
        Timbre = self.env['cfdi.timbres.sat']
        currency_id = Currency.search([('name', '=', res.get('Moneda', ''))])
        if not currency_id:
            currency_id = Currency.search([('name', '=', 'MXN')])
        timbre_id = Timbre.create({
            'name': res.get('UUID', ''),
            'cfdi_supplier_rfc': res.get('RfcEmisor', ''),
            'cfdi_customer_rfc': res.get('RfcReceptor', ''),
            'cfdi_amount': float(res.get('Total', '0.0')),
            'cfdi_certificate': res.get('NoCertificado', ''),
            'cfdi_certificate_sat': res.get('NoCertificadoSAT', ''),
            'time_invoice': res.get('Fecha', ''),
            'time_invoice_sat': res.get('FechaTimbrado', ''),
            'currency_id': currency_id and currency_id.id or False,
            'cfdi_type': res.get('TipoDeComprobante', ''),
            'cfdi_pac_rfc': res.get('RfcProvCertif', ''),
            'cfdi_cadena_ori': res.get('cadenaOri', ''),
            'cfdi_cadena_sat': res.get('cadenaSat', ''),
            'cfdi_sat_status': "valid",
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id
        })
        # Adjuntos
        xname = "%s.xml"%res.get('UUID', '')
        attachment_values = {
            'name':  xname,
            'datas': res.get('xml'),
            'datas_fname': xname,
            'description': 'Comprobante Fiscal Digital',
            'res_model': 'cfdi.timbres.sat',
            'res_id': timbre_id.id,
            'type': 'binary'
        }
        attachment_obj.create(attachment_values)
        values = {
            'cadena': res.get('cadenaori', ''),
            'fecha_timbrado': res.get('fecha'),
            'sello_sat': res.get('satSeal'),
            'certificado_sat': res.get('noCertificadoSAT'),
            'sello': res.get('SelloCFD'),
            'noCertificado': res.get('NoCertificado'),
            'uuid': res.get('UUID') or res.get('uuid') or '',
            'qrcode': res.get('qr_img'),
            'mensaje_pac': res.get('Leyenda'),
            'tipo_cambio': res.get('TipoCambio'),
            'cadena_sat': res.get('cadena_sat'),
            'test': res.get('test')
        }
        self.write({
            'cfdi_timbre_id': timbre_id.id
        })
        return True
        

    @api.multi
    def cfdi_payment_comprobante(self):
        self.ensure_one()
        date_invoice = self.date_invoice_cfdi
        if not date_invoice:
            date_invoice_cfdi = self._compute_date_invoice_cfdi()
        folio_serie = self._get_folio(self.name)
        folio = folio_serie.get("folio")
        serie = folio_serie.get("serie")       
        Comprobante = collections.OrderedDict()
        Comprobante['@xmlns:cfdi'] = 'http://www.sat.gob.mx/cfd/3'
        Comprobante['@xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        Comprobante['@xsi:schemaLocation'] = 'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd http://www.sat.gob.mx/Pagos http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos10.xsd'
        Comprobante['@xmlns:pago10'] = 'http://www.sat.gob.mx/Pagos'
        Comprobante['@Version'] = '3.3'
        if self.journal_id.serie:
            Comprobante['@Serie'] = get_string_cfdi(serie or '', 25) or False
        Comprobante['@Folio'] = get_string_cfdi(folio or '', 40) or ""
        Comprobante['@Fecha'] = date_invoice
        Comprobante['@NoCertificado'] = ""
        Comprobante['@Certificado'] = ""
        Comprobante['@SubTotal'] = "0"
        Comprobante['@Moneda'] = "XXX"
        Comprobante['@Total'] = "0"
        Comprobante['@TipoDeComprobante'] = "P"
        Comprobante['@LugarExpedicion'] = self.journal_id.codigo_postal_id.name or ""
        return Comprobante

    @api.multi
    def cfdi_payment_relacionados(self):
        self.ensure_one()
        Relacionados = collections.OrderedDict()
        Relacionados["@TipoRelacion"] = "04"
        CfdiRelacionado = []
        Relacionado = collections.OrderedDict()
        Relacionado["@UUID"] = self.cfdi_timbre_id.name
        CfdiRelacionado.append(Relacionado)
        Relacionados["cfdi:CfdiRelacionado"] = CfdiRelacionado
        return Relacionados

    @api.multi
    def cfdi_payment_emisor(self):
        self.ensure_one()
        partner_data = self.company_id.partner_id
        Emisor = collections.OrderedDict()
        Emisor["@Rfc"] = partner_data.vat or ""
        Emisor["@Nombre"] = partner_data.name or ""
        Emisor["@RegimenFiscal"] = partner_data.regimen_id and partner_data.regimen_id.clave or ""
        return Emisor

    @api.multi
    def cfdi_payment_receptor(self):
        self.ensure_one()
        partner_data = self.partner_id
        Receptor = collections.OrderedDict()
        Receptor["@Rfc"] = partner_data.vat or ""
        Receptor["@Nombre"] = partner_data.name or ""
        Receptor["@UsoCFDI"] = "P01"
        if partner_data.es_extranjero == True:
            Receptor['ResidenciaFiscal'] = partner_data.country_id and partner_data.country_id.code_alpha3 or ''
            if partner_data.identidad_fiscal:
                Receptor['NumRegIdTrib'] = partner_data.identidad_fiscal or ''
        return Receptor

    @api.multi
    def cfdi_payment_conceptos(self):
        self.ensure_one()
        Conceptos = collections.OrderedDict()
        concepto = []
        item = collections.OrderedDict()
        item["@ClaveProdServ"] = "84111506"
        item["@Cantidad"] = 1
        item["@ClaveUnidad"] = "ACT"
        item["@Descripcion"] = "Pago"
        item["@ValorUnitario"] = "0"
        item["@Importe"] = "0"
        concepto.append(item)
        Conceptos["cfdi:Concepto"] = concepto
        return Conceptos

    @api.multi
    def cfdi_payment_complemento(self):
        self.ensure_one()

        MoveLine = self.env['account.move.line']
        decimal_precision = self.env['decimal.precision'].precision_get('Account')

        mxn = self.env.ref('base.MXN')
        rate = ('%.6f' % (self.currency_id.with_context(date=self.payment_date).compute( 1, mxn, False))) if self.currency_id.name != 'MXN' else False
        DoctoRelacionado = []
        Pago10 = []
        pago = collections.OrderedDict()
        pago["@FechaPago"]= '%sT12:00:00'%(self.payment_date)
        pago["@FormaDePagoP"]= self.formapago_id.clave or "01"
        pago["@MonedaP"]= self.currency_id.name
        if self.currency_id.name != "MXN":
            pago["@TipoCambioP"] = rate
        pago["@Monto"]= '%.*f' % (decimal_precision, self.amount)
        pago["@NumOperacion"]= self.communication or ""

        if self.formapago_id and self.formapago_id.banco:
            if self.cta_origen_id:
                bank_vat = self.cta_origen_id and self.cta_origen_id.bank_id or False
                if bank_vat and bank_vat and bank_vat.vat:
                    pago["@RfcEmisorCtaOrd"] = bank_vat and bank_vat.vat or ""
                    pago["@CtaOrdenante"]= self.cta_origen_id.acc_number or ""
                    if bank_vat.vat == "XEXX010101000":
                        pago["@NomBancoOrdExt"] = bank_vat.description or ""

            bank_vat = self.journal_id and self.journal_id.bank_id and self.journal_id.bank_id.vat or False
            if bank_vat:
                pago["@RfcEmisorCtaBen"] = bank_vat
                pago["@CtaBeneficiario"] = self.journal_id and self.journal_id.bank_acc_number or ""

            if self.spei_tipo_cadenapago == "01":
                pago["@TipoCadPago"] = self.spei_tipo_cadenapago
                pago["@CertPago"] = self.spei_certpago
                pago["@CadPago"] = self.spei_cadpago
                pago["@SelloPago"] = self.spei_sellopago

        DoctoRelacionado = []
        write_off = self.move_line_ids.filtered(lambda l: l.account_id == self.writeoff_account_id and l.name == self.writeoff_label)
        for invoice in self.invoice_ids:
            payments_widget = json.loads(invoice.payments_widget)
            amount = [p for p in payments_widget.get("content", []) if p.get('account_payment_id', False) == self.id]
            amount = amount[0].get('amount', 0.0) if amount else 0.0
            write_off = (write_off.amount_currency if invoice.currency_id.name != 'MXN' else write_off.debit) if write_off else 0
            balance = invoice.residual + amount
            amount = amount - write_off
            residual = balance - amount if balance - amount > 0 else 0
            inv_rate = ('%.6f' % (invoice.currency_id.with_context(date=self.payment_date).compute(1, self.currency_id, round=False))) if self.currency_id != invoice.currency_id else False
            # inv_rate = 1 if inv_rate and invoice.currency_id.name == 'MXN' else inv_rate

            docto_attribs = collections.OrderedDict()
            docto_attribs["@IdDocumento"] = "%s"%invoice.uuid
            docto_attribs["@Folio"] = "%s"%invoice.number
            docto_attribs["@MonedaDR"] = "%s"%invoice.currency_id.name
            docto_attribs["@MetodoDePagoDR"] = '%s'%(invoice.metodopago_id and invoice.metodopago_id.clave or "PPD")
            docto_attribs["@NumParcialidad"] = len(invoice.payment_ids.filtered(lambda p: p.state not in ('draft', 'cancelled')).ids)
            docto_attribs["@ImpSaldoAnt"] = '%0.*f' % (decimal_precision, balance)
            docto_attribs["@ImpPagado"] = '%0.*f' % (decimal_precision, amount)
            docto_attribs["@ImpSaldoInsoluto"] = '%0.*f' % (decimal_precision, residual)
            if invoice.journal_id.serie:
                docto_attribs['@Serie'] = invoice.journal_id.serie or ''
            if inv_rate:
                docto_attribs['@TipoCambioDR'] = inv_rate
            DoctoRelacionado.append(docto_attribs)

        pago["pago10:DoctoRelacionado"] = DoctoRelacionado
        Pago10.append(pago)

        Pagos = collections.OrderedDict()
        Pagos["pago10:Pago"] = Pago10

        Complemento = collections.OrderedDict()
        Complemento["pago10:Pagos"] = Pagos
        Complemento["pago10:Pagos"]["@Version"] = "1.0"
        
        return Complemento

    @staticmethod
    def _get_folio(number):
        values = {'serie': None, 'folio': None}
        number_matchs = [rn for rn in re.finditer('\d+', number or '')]
        if number_matchs:
            last_number_match = number_matchs[-1]
            values['serie'] = number[:last_number_match.start()] or None
            values['folio'] = last_number_match.group().lstrip('0') or None
        return values

    # Cancel
    @api.multi
    def cancel(self):
        res = super(AccountPayment, self).cancel()
        for record in self.filtered(lambda r: r.cfdi_is_required()):
            if self.cfdi_timbre_id:
                res = record.action_cancel_cfdi()
                if res.get('message'):
                    message = res['message']
                    record.message_post(body=message)
                    raise UserError(message)
                else:
                    self.get_process_cancel_data(res.get('result'))
        return res

    @api.multi
    def action_cancel_cfdi(self):
        self.ensure_one()
        if self.cfdi_timbre_id:
            url = "%s/cfdi/cancel/%s/%s"%(self.company_id.cfd_mx_host, self.company_id.cfd_mx_db, self.company_id.vat)
            headers = {'Content-Type': 'application/json'}
            data = {
                "params": {
                    "test": self.company_id.cfd_mx_test,
                    "pac": self.company_id.cfd_mx_pac,
                    "version": self.company_id.cfd_mx_version,
                    "cfdi": {
                        "uuid": self.cfdi_timbre_id.name,
                        'noCertificado': self.cfdi_timbre_id.cfdi_certificate
                    }
                }
            }
            data_json = json.dumps(data)
            res = requests.post(url=url, data=data_json, headers=headers)
            res_datas = res.json()
            msg = res_datas.get('error') and res_datas['error'].get('data') and res_datas['error']['data'].get('message')
            if msg:
                return res_datas['error']['data']
            if res_datas.get('error'):
                return res_datas['error']
            if res_datas.get('result') and res_datas['result'].get('error'):
                return res_datas['result']['error']
            return res_datas
        return {}

    def get_process_cancel_data(self, res):
        self.cfdi_timbre_id.write({
            "cfdi_cancel_date_sat": res.get("Fecha"),
            "cfdi_cancel_status_sat": res.get("EstatusCancelacion"),
            "cfdi_cancel_code_sat": res.get("MsgCancelacion"),
            "cfdi_sat_status": res.get("Status"),
            "partner_id": self.partner_id.id,
            "journal_id": self.journal_id.id
        })
        if res.get("Acuse"):
            attachment_obj = self.env['ir.attachment']
            fname = "cancelacion_cfd_%s.xml"%(self.cfdi_timbre_id.name or "")
            attachment_values = {
                'name': fname,
                'datas': base64.b64encode( res["Acuse"] ),
                'datas_fname': fname,
                'description': 'Cancelar Comprobante Fiscal Digital',
                'res_model': "cfdi.timbres.sat",
                'res_id': self.cfdi_timbre_id.id,
                'type': 'binary'
            }
            attachment_obj.create(attachment_values)
        return True




class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    hide_formapago_id = fields.Boolean(compute='_compute_hide_formapago_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')
    formapago_code = fields.Char(related='formapago_id.clave')
    spei_tipo_cadenapago = fields.Selection([
            ('01', 'SPEI')
        ], string="Tipo de Cadena de Pago", domain=[('formapago_id.clave', '!=', '03')],
        help="Se debe registrar la clave del tipo de cadena de pago que genera la entidad receptora del pago.", default="")
    spei_certpago = fields.Text(string="Certificado Pago SPEI")
    spei_cadpago = fields.Text(string="Cadena Pago SPEI")
    spei_sellopago = fields.Text(string="Sello Pago SPEI")

    @api.one
    @api.depends('journal_id')
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids:
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        move = super(AccountBankStatementLine, self).process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        if not self.cfdi_is_required():
            return move
        invoice_ids = []
        for aml in move.line_ids:
            if aml.credit > 0:
                for r in aml.matched_debit_ids:
                    inv_id = r.debit_move_id.invoice_id
                    if inv_id:
                        if inv_id.uuid and inv_id.type == 'out_invoice':
                            invoice_ids.append(inv_id.id)
            else:
                for r in aml.matched_credit_ids:
                    inv_id = r.credit_move_id.invoice_id
                    if inv_id:
                        if inv_id.uuid and inv_id.type == 'out_invoice':
                            invoice_ids.append(inv_id.id)
        payments = move.mapped('line_ids.payment_id')
        payment_method = self.formapago_id and self.formapago_id.id
        payments.write({
            'formapago_id': payment_method,
            'invoice_ids': [(6, 0, invoice_ids)]
        })
        payments.action_validate_cfdi()
        return move

    @api.multi
    def cfdi_is_required(self):
        self.ensure_one()
        required = (
            self.journal_id.id in self.env.user.company_id.cfd_mx_journal_ids.ids
        )
        if getattr(self, 'pos_statement_id', False):
            return False
        return required


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ['mail.thread', 'account.move.line', 'account.cfdi']

    uuid = fields.Char(string='Timbre fiscal', related='payment_id.cfdi_timbre_id.name')
    date_invoice = fields.Date(string='Invoice Date')

    @api.multi
    def get_xml(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            xml_id = self.env["ir.attachment"].search([('res_model', '=', 'cfdi.timbres.sat'), ('res_id', '=', self.payment_id.cfdi_timbre_id.id), ('type', '=', 'binary'), ('name', 'ilike', '%s.xml'%(self.uuid) )])
            url = '/web/content/%s?download=true'%(xml_id.id)
            return {
                'type': 'ir.actions.act_url',
                'url':url,
                'nodestroy': True
            }
        else:
            raise UserError("No es una Factura CFDI de Pago")

    @api.multi
    def get_pdf(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            print "self.payment_id.cfdi_timbre_id", self.payment_id.cfdi_timbre_id
            return self.env['report'].get_action(self.payment_id.cfdi_timbre_id, 'complemento_pagos.report_cfdipagosmx')
        else:
            raise UserError("No es una Factura CFDI de Pago")

    @api.multi
    def get_email(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            template = self.env.ref('complemento_pagos.email_template_payment_receipt', False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='account.payment',
                default_res_id=self.payment_id.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
                mark_invoice_as_sent=True,
                cfdi_timbre_id=self.payment_id.cfdi_timbre_id.id,
                custom_layout="complemento_pagos.email_notification_paynow"
            )
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }

        else:
            raise UserError("No es una Factura CFDI de Pago")



    @api.multi
    def get_xml_cfdi(self):
        nodosPagos = []
        timbreAtrib = {}
        compAtrib = {}
        receptorAtrib = {}
        emisorAtrib = {}
        xml = False
        att_obj = self.env['ir.attachment']
        for rec in self:
            att_ids = att_obj.search([('res_model', '=', 'account.move.line'), ('res_id', '=', rec.id), ('type', '=', 'binary')])
            for att_id in att_ids:
                xml = att_id.datas
                cfdi = base64.b64decode(att_id.datas)
                xmlDoc = parseString(cfdi)
                nodes = xmlDoc.childNodes
                comprobante = nodes[0]
                compAtrib = dict(comprobante.attributes.items())

                emisor = comprobante.getElementsByTagName('cfdi:Emisor')
                emisorAtrib = dict(emisor[0].attributes.items())

                receptor = comprobante.getElementsByTagName('cfdi:Receptor')
                receptorAtrib = dict(receptor[0].attributes.items())

                complementos = comprobante.getElementsByTagName('cfdi:Complemento')
                for comp in complementos:
                    timbreFiscal = comp.getElementsByTagName('tfd:TimbreFiscalDigital')
                    for timbre in timbreFiscal:
                        timbreAtrib = dict(timbre.attributes.items())

                    pagos10 = comp.getElementsByTagName('pago10:Pagos')
                    for pago10 in pagos10:
                        pagos = pago10.getElementsByTagName('pago10:Pago')
                        for pago in pagos:
                            pagoAtrib = dict(pago.attributes.items())
                            doctosAtrib = []
                            rels = pago.getElementsByTagName('pago10:DoctoRelacionado')
                            for rel in rels:
                                relAtrib = dict(rel.attributes.items())
                                doctosAtrib.append(relAtrib)
                            nodosPagos.append({
                                'pagosAtrib': pagoAtrib,
                                'doctosAtrib': doctosAtrib
                            })
        return {
            'compAtrib': compAtrib,
            'receptorAtrib': receptorAtrib,
            'emisorAtrib': emisorAtrib,
            'nodosPagos': nodosPagos,
            'timbreAtrib': timbreAtrib,
            'xml': xml
        }


    @api.multi
    def getElectronicPayment(self):
        Timbre = self.env["cfdi.timbres.sat"]
        Attachment = self.env['ir.attachment']
        for moveline_id in self:
            if moveline_id.payment_id:
                payment_id = moveline_id.payment_id
                attrs = moveline_id.get_xml_cfdi()
                if attrs and attrs.get("compAtrib") and attrs["compAtrib"].get("Sello"):
                    xml = attrs["xml"]
                    compAtrib = attrs["compAtrib"]
                    timbreAtrib = attrs["timbreAtrib"]
                    emisorAtrib = attrs["emisorAtrib"]
                    receptorAtrib = attrs["receptorAtrib"]
                    uuid = timbreAtrib.get('UUID')
                    timbre_ids = Timbre.search([('name', '=', uuid)])
                    _logger.info("UUID: %s"%uuid)
                    if not timbre_ids:
                        timbre_id = Timbre.sudo().create({
                            "name": timbreAtrib.get('UUID'),
                            "cfdi_supplier_rfc": emisorAtrib.get('Rfc', ''),
                            "cfdi_customer_rfc": receptorAtrib.get('Rfc', ''),
                            "cfdi_amount": float(timbreAtrib.get('Total', '0.0')),
                            "cfdi_certificate": compAtrib.get('NoCertificado', ''),
                            "cfdi_certificate_sat": timbreAtrib.get('NoCertificadoSAT', ''),
                            "time_invoice": compAtrib.get('Fecha', ''),
                            "time_invoice_sat": timbreAtrib.get('FechaTimbrado', ''),
                            'currency_id': payment_id.currency_id and payment_id.currency_id.id or False,
                            'cfdi_type': compAtrib.get('TipoDeComprobante', 'P'),
                            "cfdi_pac_rfc": timbreAtrib.get('RfcProvCertif', ''),
                            "cfdi_cadena_ori": "",
                            'cfdi_cadena_sat': self.cadena_sat,
                            'cfdi_sat_status': "valid",
                            'journal_id': payment_id.journal_id.id,
                            'partner_id': payment_id.partner_id.id
                        })
                        # Adjuntos
                        xname = "%s.xml"%uuid
                        attachment_values = {
                            'name':  xname,
                            'datas': xml,
                            'datas_fname': xname,
                            'description': 'Comprobante Fiscal Digital',
                            'res_model': 'cfdi.timbres.sat',
                            'res_id': timbre_id.id,
                            'type': 'binary'
                        }
                        Attachment.sudo().create(attachment_values)
                        payment_id.sudo().write({
                            'cfdi_timbre_id': timbre_id.id
                        })

        return True



class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposeMessage, self).onchange_template_id(template_id,
                composition_mode, model, res_id)

        if model=='account.payment':
            payment_id = self.env[model].browse( res_id )
            if payment_id and payment_id.cfdi_timbre_id:
                xml_id = self.env["ir.attachment"].search([('name', '=', '%s.xml'%payment_id.cfdi_timbre_id.name )])
                if xml_id:
                    res['value'].setdefault('attachment_ids', []).append(xml_id[0].id)

        return res

