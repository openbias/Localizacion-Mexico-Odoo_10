# -*- coding: utf-8 -*-

from xml.dom import minidom
from xml.dom.minidom import parse, parseString

from datetime import date, datetime
from pytz import timezone
import json, base64, re
import collections, requests
import logging

from lxml import etree
from lxml.objectify import fromstring

import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.exceptions import UserError, RedirectWarning, ValidationError

from .nodo import Nodo

# _logger = logging.basicConfig(level=logging.INFO)
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


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _description = 'Bank Accounts'

    factoring = fields.Boolean(string="Es Factoraje", default=False)

class AccountAbstractPayment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.one
    @api.depends('journal_id')
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        country_code = self.company_id.partner_id.country_id and self.company_id.partner_id.country_id.code
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids and self.partner_type == "customer" and country_code=="MX":
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True

    @api.one
    @api.depends('cta_origen_id')
    def _compute_hide_cfdi_factoraje_id(self):
        if not self.cta_origen_id:
            self.hide_cfdi_factoraje_id = True
            return
        self.partner_factoraje_id = self.cta_origen_id.partner_id
        if self.cta_origen_id.factoring:
            self.hide_cfdi_factoraje_id = False
        else:
            self.hide_cfdi_factoraje_id = True

    cta_destino_id = fields.Many2one('res.partner.bank', string='Cuenta Destino', oldname="cta_destino")
    cta_origen_id = fields.Many2one('res.partner.bank', string='Cuenta Origen', oldname="cta_origen")
    cta_destino_partner_id = fields.Many2one('res.partner', string='Partner Cuenta Destino', oldname="cta_destino_partner")
    cta_origen_partner_id = fields.Many2one('res.partner', string='Partner Cuenta Origen', oldname="cta_origen_partner")
    hide_formapago_id = fields.Boolean(compute='_compute_hide_formapago_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')
    formapago_code = fields.Char(related='formapago_id.clave')
    cfdi_factoraje_id = fields.Many2one('account.invoice', string=u'CFDI Factoraje Compensacion')
    partner_factoraje_id = fields.Many2one('res.partner', string=u'Empresa Factoraje', store=True, compute='_compute_hide_cfdi_factoraje_id')
    hide_cfdi_factoraje_id = fields.Boolean(compute='_compute_hide_cfdi_factoraje_id',
        help="Este campo es usado para ocultar el cfdi_factoraje_id, cuando no se trate de una cuenta origen de Factoraje")

    @api.onchange('journal_id')
    def _onchange_journal(self):
        rec = super(AccountAbstractPayment, self)._onchange_journal()
        if not self.journal_id:
            rec['cta_origen_id'] = False
            rec['cta_destino_id'] = False
        if rec and self.partner_id and self.journal_id and self.partner_type:
            if self.journal_id.type == 'cash':
                # self.tipo_pago = 'otro'
                self.metodo_pago_id = self.env.ref('contabilidad_electronica.metodo_pago_1')
                self.formapago_id = self.env.ref('cfd_mx.formapago_01')
            elif self.journal_id.type == 'bank':
                # self.tipo_pago = 'trans'
                self.metodo_pago_id = self.env.ref('contabilidad_electronica.metodo_pago_3')
                self.formapago_id = self.env.ref('cfd_mx.formapago_03')
            bank_ids = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            jb_ids = self.journal_id.bank_account_id
            if self.partner_type == "customer":
                self.benef_id = self.company_id.partner_id
                self.cta_destino_id = jb_ids.ids
                if self.hide_formapago_id == False:
                    factoring_ids = self.env['res.partner.bank'].search([('factoring', '=', True)])
                    bank_ids |= factoring_ids
                rec['domain']['cta_origen_id'] = [('id', 'in', bank_ids.ids)]
                rec['domain']['cta_destino_id'] = [('id', 'in', jb_ids.ids)]
            else:
                self.benef_id = self.partner_id
                self.cta_origen_id = jb_ids.ids
                rec['domain']['cta_origen_id'] = [('id', 'in', jb_ids.ids)]
                rec['domain']['cta_destino_id'] = [('id', 'in', bank_ids.ids)]
        return rec


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"
    _description = "Register payments on multiple invoices"

    spei_tipo_cadenapago = fields.Selection([
            ('01', 'SPEI')
        ], string="Tipo de Cadena de Pago", domain=[('formapago_id.clave', '!=', '03')],
        help="Se debe registrar la clave del tipo de cadena de pago que genera la entidad receptora del pago.", default="")
    spei_certpago = fields.Text(string="Certificado Pago SPEI")
    spei_cadpago = fields.Text(string="Cadena Pago SPEI")
    spei_sellopago = fields.Text(string="Sello Pago SPEI")

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
        if self.date_invoice_cfdi:
            return
        tz = self.env.user.tz or "America/Mexico_City"
        hora_factura_utc = datetime.now(timezone("UTC"))
        dtz = hora_factura_utc.astimezone(timezone(tz)).strftime("%Y-%m-%d %H:%M:%S")
        dtz = dtz.replace(" ", "T")
        self.date_invoice_cfdi = dtz

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


    @api.constrains('cta_origen_id')
    def _check_cta_origen_id(self):
        for record in self:
            if record.cta_origen_id:
                if self.formapago_id and self.journal_id and self.cta_origen_id:
                    len_cta_ori = len(self.cta_origen_id.acc_number or "")
                    if self.formapago_id.clave == '02' and len_cta_ori not in [11, 18]:
                        raise ValidationError("La Cuenta Origen para 'Cheque nominativo' debe tener 11 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '03' and len_cta_ori not in [10, 16, 18]:
                        raise ValidationError("La Cuenta Origen para 'Transferencia Electronica de Fondos' debe tener 10 o 16 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '04' and len_cta_ori not in [16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de credito' debe tener 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '05' and len_cta_ori not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Origen para 'Monedero electronico' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '06' and len_cta_ori not in [10]:
                        raise ValidationError("La Cuenta Origen para 'Dinero electronico' debe tener 10 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '28' and len_cta_ori not in [16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de debito' debe tener 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '29' and len_cta_ori not in [15, 16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de servicios' debe tener 15 o 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )

    @api.constrains('cta_destino_id')
    def _check_cta_destino_id(self):
        for record in self:
            if record.cta_destino_id:
                if self.formapago_id and self.journal_id and self.cta_destino_id:
                    len_cta_dest = len(self.cta_destino_id.acc_number or "")
                    if self.formapago_id.clave == '02' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Cheque nominativo' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '03' and len_cta_dest not in [10, 18]:
                        raise ValidationError("La Cuenta Destino para 'Transferencia Electronica de Fondos' debe tener 10 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '04' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de credito' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '05' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Monedero electronico' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    # if self.formapago_id.clave == '06' and len_cta_dest not in [10]:
                    #     raise ValidationError("La Cuenta Destino para 'Dinero electronico' debe tener 10 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '28' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de debito' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '29' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de servicios' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )


    @api.multi
    def post(self):
        ctx_inv = {}
        for record in self.filtered(lambda r: r.cfdi_validate_required()):
            for inv in record.invoice_ids:
                ctx_inv[inv.id] = {
                    'amount_total': inv.amount_total,
                    'amount_total_company_signed': inv.amount_total_company_signed,
                    'amount_total_signed': inv.amount_total_signed,
                    'residual': inv.residual if inv.residual != 0.0 else inv.amount_total,
                    'residual_company_signed': inv.residual_company_signed,
                    'residual_signed': inv.residual_signed
                }
            pass
        res = super(AccountPayment, self).post()
        for record in self.filtered(lambda r: r.cfdi_is_required()):
            record.with_context(ctx_inv=ctx_inv).action_validate_cfdi()
        return res

    @api.multi
    def cfdi_is_required(self):
        self.ensure_one()
        required = (
            self.partner_id and
            self.partner_type == "customer" and 
            self.payment_type == 'inbound' and
            self.invoice_ids.filtered(lambda i: i.type == 'out_invoice') and 
            self.journal_id.id in self.env.user.company_id.cfd_mx_journal_ids.ids
        )
        if not required:
            return required
        return required

    @api.multi
    def cfdi_validate_required(self):
        self.ensure_one()
        required = self.cfdi_is_required()
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
        if not self.communication:
            raise UserError(_('No se especifico el "Concepto de Pago"'))
        if self.cfdi_factoraje_id and self.partner_factoraje_id and not self.company_id.journal_factoring_id:
            raise UserError(_('No se especifico el "Diario de Factoraje"'))
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
                if rec.cfdi_factoraje_id and rec.partner_factoraje_id:
                    # Se cancela Factura de Proveedor Factoraje    
                    amount_total = rec.cfdi_factoraje_id.amount_total
                    self.payment_difference_factoring()
                    ctx = {'active_id': rec.cfdi_factoraje_id.id, 'active_ids': [rec.cfdi_factoraje_id.id], 'model': 'account.invoice'}
                    res = self.env['account.invoice.refund'].with_context(**ctx).create({
                        'date_invoice': rec.payment_date,
                        'description': 'Cancelar Factoraje',
                        'filter_refund': 'cancel'
                    }).invoice_refund()

        return True

    @api.multi
    def payment_difference_factoring(self):
        self.ensure_one()
        invoice_id = False
        for invoice in self.invoice_ids:
            if invoice.residual == 0.0:
                continue
            invoice_id = invoice
        journal_id = self.company_id.journal_factoring_id
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        invoice_currency = self.cfdi_factoraje_id.currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(-(self.cfdi_factoraje_id.amount_total), self.currency_id, self.company_id.currency_id, invoice_currency)
        move_vals = {
            'name': journal_id.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id(),
            'date': self.payment_date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal_id.id,
        }
        move = self.env['account.move'].create(move_vals)
        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_id))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        if counterpart_aml:
            invoice_id.register_payment(counterpart_aml)
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            vals = {
                'name': _('Counterpart'),
                'account_id': self.payment_type in ('outbound','transfer') and journal_id.default_debit_account_id.id or journal_id.default_credit_account_id.id,
                'payment_id': self.id,
                'journal_id': journal_id.id,
                'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            }
            liquidity_aml_dict.update(vals)
            aml_obj.create(liquidity_aml_dict)
            move.post()
        return True

    @api.multi
    def create_cfdi_payment(self):
        self.ensure_one()

        Comprobante = self.cfdi_comprobante()
        if self.cfdi_timbre_id:
            Comprobante = self.cfdi_relacionados(Comprobante)
        Comprobante = self.cfdi_emisor(Comprobante)
        Comprobante = self.cfdi_receptor(Comprobante)
        Comprobante = self.cfdi_conceptos(Comprobante)
        Comprobante = self.cfdi_complemento(Comprobante)
        xml = Comprobante.toxml(header=False)
        tree = fromstring(xml)
        xml = etree.tostring(tree, pretty_print=True, encoding='UTF-8')
        # print xml
        url = "%s/cfdi/stamp/%s/%s"%(self.company_id.cfd_mx_host, self.company_id.cfd_mx_db, self.company_id.vat)
        headers = {'Content-Type': 'application/json'}
        data = {
            "params": {
                "test": self.company_id.cfd_mx_test,
                "pac": self.company_id.cfd_mx_pac,
                "version": self.company_id.cfd_mx_version,
                "cfdi": base64.encodestring(Comprobante.toxml().encode('utf-8'))
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
            'partner_id': self.partner_id.id,
            'test': self.company_id.cfd_mx_test,
            'payment_id': self.id
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
    def cfdi_comprobante(self):
        self.ensure_one()
        date_invoice = self.date_invoice_cfdi
        if not date_invoice:
            date_invoice_cfdi = self._compute_date_invoice_cfdi()
        folio_serie = self._get_folio(self.name)
        folio = folio_serie.get("folio")
        serie = folio_serie.get("serie")
        cfdi_comprobante = {
            'xmlns:cfdi': 'http://www.sat.gob.mx/cfd/3',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd http://www.sat.gob.mx/Pagos http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos10.xsd',
            'xmlns:pago10': 'http://www.sat.gob.mx/Pagos',
            'Version': '3.3',
            'Serie': get_string_cfdi(serie or '', 25) or ' ',
            'Folio': get_string_cfdi(serie or '', 40) or ' ',
            'Fecha': date_invoice,
            'NoCertificado': "",
            'Certificado': "",
            'SubTotal': "0",
            'Moneda': "XXX",
            'Total': "0",
            'TipoDeComprobante': "P",
            'LugarExpedicion': self.journal_id.codigo_postal_id.name or "",
        }
        Comprobante = Nodo('cfdi:Comprobante', cfdi_comprobante)
        return Comprobante

    @api.multi
    def cfdi_relacionados(self, Comprobante):
        self.ensure_one()
        CfdiRelacionados = Nodo('cfdi:CfdiRelacionados', {'TipoRelacion': '04'}, Comprobante)
        CfdiRelacionado = Nodo('cfdi:CfdiRelacionado', {'UUID': self.cfdi_timbre_id.name}, CfdiRelacionados)
        return Comprobante

    @api.multi
    def cfdi_emisor(self, Comprobante):
        self.ensure_one()
        partner_data = self.company_id.partner_id
        emisor_attribs = {
            'Rfc': partner_data.vat or "",
            'Nombre': partner_data.name or "",
            "RegimenFiscal": partner_data.regimen_id and partner_data.regimen_id.clave or ""
        }
        Nodo('cfdi:Emisor', emisor_attribs, Comprobante)
        return Comprobante

    @api.multi
    def cfdi_receptor(self, Comprobante):
        self.ensure_one()
        partner_data = self.partner_id
        if self.partner_factoraje_id:
            partner_data = self.partner_factoraje_id
        receptor_attribs = {
            'Rfc': partner_data.vat or "",
            'Nombre': partner_data.name or "",
            'UsoCFDI': 'P01'
        }
        if partner_data.es_extranjero == True:
            receptor_attribs['ResidenciaFiscal'] = partner_data.country_id and partner_data.country_id.code_alpha3 or ''
            if partner_data.identidad_fiscal:
                receptor_attribs['NumRegIdTrib'] = partner_data.identidad_fiscal or ''
        Nodo('cfdi:Receptor', receptor_attribs, Comprobante)
        return Comprobante

    @api.multi
    def cfdi_conceptos(self, Comprobante):
        self.ensure_one()
        Conceptos = Nodo('cfdi:Conceptos', padre=Comprobante)
        concepto_attribs = {
            "ClaveProdServ": "84111506",
            "Cantidad": "1",
            "ClaveUnidad": "ACT",
            "Descripcion": "Pago",
            "ValorUnitario": "0",
            "Importe": "0",
        }
        Concepto = Nodo('cfdi:Concepto', concepto_attribs, Conceptos)
        return Comprobante

    @api.multi
    def cfdi_complemento(self, Comprobante):
        self.ensure_one()
        context = dict(self._context) or {}
        ctx_inv = context.get('ctx_inv', {})
        MoveLine = self.env['account.move.line']
        decimal_precision = self.env['decimal.precision'].precision_get('Account')
        mxn = self.env.ref('base.MXN')
        rate = ('%.6f' % (self.currency_id.with_context(date=self.payment_date).compute( 1, mxn, False))) if self.currency_id.name != 'MXN' else False
        nodoPago10 = []
        # Nodo pago10:Pago
        Complemento = Nodo('cfdi:Complemento', padre=Comprobante)
        Pagos = Nodo('pago10:Pagos', {"Version": '1.0'}, padre=Complemento)

        pago_attribs = {
            "FechaPago": '%sT12:00:00'%(self.payment_date),
            "FormaDePagoP": self.formapago_id.clave or "01",
            "MonedaP": self.currency_id.name,
            "Monto": '%.*f' % (decimal_precision, self.amount),
            "NumOperacion": self.communication[:100].replace('|', ' ') if self.communication else "Pago %s "%(self.payment_date)
        }
        if self.currency_id.name != "MXN":
            pago_attribs["TipoCambioP"] = rate
        if not self.cfdi_factoraje_id:
            if self.formapago_id and self.formapago_id.banco:
                if self.cta_origen_id:
                    if self.cta_origen_id and self.cta_origen_id.acc_number:
                        pago_attribs["CtaOrdenante"]= self.cta_origen_id.acc_number or ""
                    bank_vat = self.cta_origen_id and self.cta_origen_id.bank_id or False
                    if bank_vat and bank_vat.vat:
                        pago_attribs["RfcEmisorCtaOrd"] = bank_vat and bank_vat.vat or ""
                    if bank_vat and bank_vat.vat == "XEXX010101000":
                        pago_attribs["NomBancoOrdExt"] = bank_vat.description or ""
                bank_vat = self.journal_id and self.journal_id.bank_id and self.journal_id.bank_id.vat or False
                if bank_vat:
                    pago_attribs["RfcEmisorCtaBen"] = bank_vat
                if self.journal_id and self.journal_id.bank_acc_number:
                    pago_attribs["CtaBeneficiario"] = self.journal_id and self.journal_id.bank_acc_number or ""
                if self.spei_tipo_cadenapago == "01":
                    pago_attribs["TipoCadPago"] = self.spei_tipo_cadenapago
                    pago_attribs["CertPago"] = self.spei_certpago
                    pago_attribs["CadPago"] = self.spei_cadpago
                    pago_attribs["SelloPago"] = self.spei_sellopago
        Pago = Nodo('pago10:Pago', pago_attribs, padre=Pagos)
        MoveLine = self.env["account.move.line"]
        lines = self.move_line_ids.mapped('move_id.line_ids').filtered(lambda l: l.account_id.user_type_id.type == 'liquidity')
        amount_paid = sum(lines.mapped('amount_currency') if self.currency_id.name != 'MXN' else lines.mapped('debit'))
        inv_fact = {}
        for invoice in self.invoice_ids:
            inv = ctx_inv.get(invoice.id) and ctx_inv[invoice.id]
            TipoCambioDR = None
            inv_currency_id = invoice.currency_id.with_context(date=invoice.date_invoice)
            payments_widget = json.loads(invoice.payments_widget)
            content = payments_widget.get("content", [])
            payment_vals = [p for p in content if p.get('account_payment_id', False) == self.id]
            move_line_id = MoveLine.browse( payment_vals[0].get('payment_id', False) )
            # print "amount_currency", abs(move_line_id.amount_currency), abs(move_line_id.credit)
            amount_payment = abs(move_line_id.amount_currency) or abs(move_line_id.credit)
            if inv_currency_id == invoice.company_id.currency_id:
                amount_payment = abs(move_line_id.credit)
                TipoCambioDR = rate
            else:
                amount_payment = abs(move_line_id.amount_currency)
            rate_difference = [p for p in content if p.get('journal_name', '') == self.company_id.currency_exchange_journal_id.name]
            rate_difference = rate_difference[0].get('amount', 0.0) if rate_difference else 0.0

            NumParcialidad = len(invoice.payment_ids.filtered(lambda p: p.state not in ('draft', 'cancelled')).ids)
            ImpSaldoAnt = inv.get('residual', 0.0)  # invoice.residual + amount_payment + rate_difference
            ImpPagado = amount_payment
            if amount_payment > ImpSaldoAnt:
                ImpPagado = ImpSaldoAnt
                ImpSaldoInsoluto = 0.0
            if self.currency_id != inv_currency_id:
                TipoCambioDR = 1
                if rate_difference:
                    ImpPagado = ImpSaldoAnt
                    ImpSaldoInsoluto = 0.0
            ImpSaldoInsoluto = ImpSaldoAnt - ImpPagado
            docto_attribs = {
                "IdDocumento": "%s"%invoice.uuid,
                "Folio": "%s"%invoice.number,
                "MonedaDR": "%s"%invoice.currency_id.name,
                "MetodoDePagoDR": 'PPD',
                "NumParcialidad": NumParcialidad,
                "ImpSaldoAnt": '%0.*f' % (decimal_precision, ImpSaldoAnt),
                "ImpPagado": '%0.*f' % (decimal_precision, ImpPagado),
                "ImpSaldoInsoluto": '%0.*f' % (decimal_precision, ImpSaldoInsoluto),
            }
            if TipoCambioDR:
                docto_attribs['TipoCambioDR'] = TipoCambioDR # ('%.6f' % (TipoCambioDR))
            DoctoRelacionado = Nodo('pago10:DoctoRelacionado', docto_attribs, padre=Pago)
            inv_fact[invoice.id] = {'uuid': invoice.uuid, 'ImpSaldoInsoluto': '%0.*f' % (decimal_precision, ImpSaldoInsoluto)}
        if self.cfdi_factoraje_id and self.partner_factoraje_id:
            for invoice in self.invoice_ids:
                if invoice.residual == 0.0:
                    continue
                amount_total = self.cfdi_factoraje_id.amount_total
                doctoRel = inv_fact.get(invoice.id)
                ImpSaldoAnt = 0.0
                if doctoRel:
                    ImpSaldoAnt = float(doctoRel.get("ImpSaldoInsoluto"))
                ImpSaldoAnt =  '%0.*f' % (decimal_precision, ImpSaldoAnt)
                amount_total = '%0.*f' % (decimal_precision, amount_total)
                ImpSaldoInsoluto = float(ImpSaldoAnt)-float(amount_total)
                pago_attribs = {
                    "FechaPago": '%sT12:00:00'%(self.payment_date),
                    "FormaDePagoP": "17",
                    "MonedaP": self.currency_id.name,
                    "Monto": amount_total,
                    "NumOperacion": "Compensacion",
                }
                if self.currency_id.name != "MXN":
                    pago_attribs["TipoCambioP"] = rate
                Pagos = Nodo('pago10:Pagos', {"Version": '1.0'}, padre=Complemento)
                Pago = Nodo('pago10:Pago', pago_attribs, padre=Pagos)
                NumParcialidad = 2
                inv_rate = ('%.6f' % (self.cfdi_factoraje_id.currency_id.with_context(date=self.payment_date).compute(1, self.currency_id, round=False))) if self.currency_id != self.cfdi_factoraje_id.currency_id else False
                docto_attribs = {
                    "IdDocumento": "%s"%invoice.uuid,
                    "Folio": "%s"%invoice.number,
                    "MonedaDR": "%s"%invoice.currency_id.name,
                    "MetodoDePagoDR": '%s'%(invoice.metodopago_id and invoice.metodopago_id.clave or "PPD"),
                    "NumParcialidad": '%s'%NumParcialidad,
                    "ImpSaldoAnt": ImpSaldoAnt,
                    "ImpPagado": amount_total,
                    "ImpSaldoInsoluto": '%0.*f' % (decimal_precision, ImpSaldoInsoluto),
                }
                if invoice.journal_id.serie:
                    docto_attribs['Serie'] = invoice.journal_id.serie or ''
                if inv_rate:
                    docto_attribs['TipoCambioDR'] = (1 / inv_rate)
                DoctoRelacionado = Nodo('pago10:DoctoRelacionado', docto_attribs, padre=Pago)
        return Comprobante


    @staticmethod
    def _get_folio(number=""):
        number = number and number.replace("/", "") or ""
        values = {'serie': "", 'folio': ""}
        number_matchs = [rn for rn in re.finditer('\d+', number or '')]
        if number_matchs:
            last_number_match = number_matchs[-1]
            values['serie'] = number[:last_number_match.start()] or ""
            values['folio'] = last_number_match.group().lstrip('0') or ""
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

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.one
    def _compute_hide_cfdi_id(self):
        if not self.journal_id:
            self.hide_cfdi_id = True
            return
        country_code = self.company_id.partner_id.country_id and self.company_id.partner_id.country_id.code
        print "country_code", country_code
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids and country_code == "MX":
            self.hide_cfdi_id = False
        else:
            self.hide_cfdi_id = True

    hide_cfdi_id = fields.Boolean(compute='_compute_hide_cfdi_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.one
    @api.depends('cta_origen_id')
    def _compute_hide_cfdi_factoraje_id(self):
        if not self.cta_origen_id:
            self.hide_cfdi_factoraje_id = True
            return
        self.partner_factoraje_id = self.cta_origen_id.partner_id
        if self.cta_origen_id.factoring:
            self.hide_cfdi_factoraje_id = False
        else:
            self.hide_cfdi_factoraje_id = True

    """
    @api.one
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        country_code = self.company_id.partner_id.country_id and self.company_id.partner_id.country_id.code
        print "country_code", country_code
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids and self.payment_type == 'inbound' and country_code == "MX":
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True
    """

    cta_destino_id = fields.Many2one("res.partner.bank", string="Cuenta destino", oldname="cta_destino")
    cta_origen_id = fields.Many2one("res.partner.bank", string="Cuenta origen", oldname="cta_origen")
    hide_formapago_id = fields.Boolean(default=True, help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')
    formapago_code = fields.Char(related='formapago_id.clave')
    spei_tipo_cadenapago = fields.Selection([
            ('01', 'SPEI')
        ], string="Tipo de Cadena de Pago", domain=[('formapago_id.clave', '!=', '03')],
        help="Se debe registrar la clave del tipo de cadena de pago que genera la entidad receptora del pago.", default="")
    spei_certpago = fields.Text(string="Certificado Pago SPEI")
    spei_cadpago = fields.Text(string="Cadena Pago SPEI")
    spei_sellopago = fields.Text(string="Sello Pago SPEI")
    cfdi_factoraje_id = fields.Many2one('account.invoice', string=u'CFDI Factoraje Compensacion')
    partner_factoraje_id = fields.Many2one('res.partner', string=u'Empresa Factoraje', store=True, compute='_compute_hide_cfdi_factoraje_id')
    hide_cfdi_factoraje_id = fields.Boolean(compute='_compute_hide_cfdi_factoraje_id',
        help="Este campo es usado para ocultar el cfdi_factoraje_id, cuando no se trate de una cuenta origen de Factoraje")


    @api.constrains('cta_origen_id')
    def _check_cta_origen_id(self):
        for record in self:
            if record.cta_origen_id:
                if self.formapago_id and self.journal_id and self.cta_origen_id:
                    len_cta_ori = len(self.cta_origen_id.acc_number or "")
                    if self.formapago_id.clave == '02' and len_cta_ori not in [11, 18]:
                        raise ValidationError("La Cuenta Origen para 'Cheque nominativo' debe tener 11 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '03' and len_cta_ori not in [10, 16, 18]:
                        raise ValidationError("La Cuenta Origen para 'Transferencia Electronica de Fondos' debe tener 10 o 16 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '04' and len_cta_ori not in [16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de credito' debe tener 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '05' and len_cta_ori not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Origen para 'Monedero electronico' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '06' and len_cta_ori not in [10]:
                        raise ValidationError("La Cuenta Origen para 'Dinero electronico' debe tener 10 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '28' and len_cta_ori not in [16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de debito' debe tener 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )
                    if self.formapago_id.clave == '29' and len_cta_ori not in [15, 16]:
                        raise ValidationError("La Cuenta Origen para 'Tarjeta de servicios' debe tener 15 o 16 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_origen_id.acc_number or ""),  self.cta_origen_id.acc_number) )

    @api.constrains('cta_destino_id')
    def _check_cta_destino_id(self):
        for record in self:
            if record.cta_destino_id:
                if self.formapago_id and self.journal_id and self.cta_destino_id:
                    len_cta_dest = len(self.cta_destino_id.acc_number or "")
                    if self.formapago_id.clave == '02' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Cheque nominativo' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '03' and len_cta_dest not in [10, 18]:
                        raise ValidationError("La Cuenta Destino para 'Transferencia Electronica de Fondos' debe tener 10 o 18 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '04' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de credito' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '05' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Monedero electronico' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    # if self.formapago_id.clave == '06' and len_cta_dest not in [10]:
                    #     raise ValidationError("La Cuenta Destino para 'Dinero electronico' debe tener 10 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '28' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de debito' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )
                    if self.formapago_id.clave == '29' and len_cta_dest not in [10, 11, 15, 16, 18, 50]:
                        raise ValidationError("La Cuenta Destino para 'Tarjeta de servicios' debe tener 10, 11, 15, 16, 18, 50 digitos.\n Digitos: %s - Cuenta: %s"%( len(self.cta_destino_id.acc_number or ""),  self.cta_destino_id.acc_number) )


    @api.onchange('partner_id', 'payment_type')
    def _onchange_payment_type_partner_id(self):
        res = {}
        warning = {}
        domain = {}
        if self.partner_id and self.journal_id and self.payment_type:
            country_code = self.company_id.partner_id.country_id and self.company_id.partner_id.country_id.code
            if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids and self.payment_type == 'inbound' and country_code == "MX":
                self.hide_formapago_id = False
            else:
                self.hide_formapago_id = True


            if self.journal_id.type == 'cash':
                # self.ttype = 'otro'
                self.metodo_pago_id = self.env.ref('contabilidad_electronica.metodo_pago_1')
                self.formapago_id = self.env.ref('cfd_mx.formapago_01')
            elif self.journal_id.type == 'bank':
                # self.ttype = 'trans'
                self.metodo_pago_id = self.env.ref('contabilidad_electronica.metodo_pago_3')
                self.formapago_id = self.env.ref('cfd_mx.formapago_03')
            bank_ids = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            jb_ids = self.journal_id.bank_account_id
            if self.payment_type == "inbound":
                self.benef_id = self.company_id.partner_id
                self.cta_destino_id = jb_ids.ids
                if self.hide_formapago_id == False:
                    factoring_ids = self.env['res.partner.bank'].search([('factoring', '=', True)])
                    bank_ids |= factoring_ids
                domain = {
                    'cta_origen_id': [('id', 'in', bank_ids.ids)],
                    'cta_destino_id': [('id', 'in', jb_ids.ids)]
                }
            else:
                self.benef_id = self.partner_id
                self.cta_origen_id = jb_ids.ids
                domain = {
                    'cta_origen_id': [('id', 'in', jb_ids.ids)],
                    'cta_destino_id': [('id', 'in', bank_ids.ids)]
                }
        if domain:
            res['domain'] = domain
        return res

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        invoice_ids = self.env['account.invoice'].browse()
        ctx_inv = {}
        for aml in counterpart_aml_dicts:
            if aml.get('move_line'):
                if aml['move_line'].invoice_id:
                    inv = aml['move_line'].invoice_id
                    if inv.type == 'out_invoice':
                        invoice_ids |= inv
                        ctx_inv[inv.id] = {
                            'amount_total': inv.amount_total,
                            'amount_total_company_signed': inv.amount_total_company_signed,
                            'amount_total_signed': inv.amount_total_signed,
                            'residual': inv.residual if inv.residual != 0.0 else inv.amount_total,
                            'residual_company_signed': inv.residual_company_signed,
                            'residual_signed': inv.residual_signed
                        }
        move = super(AccountBankStatementLine, self).process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        if not self.cfdi_is_required():
            return move

        if not invoice_ids:
            return move

        payments = move.mapped('line_ids.payment_id')
        payment_method = self.formapago_id and self.formapago_id.id
        vals = {
            'cta_destino_id': self.cta_destino_id and self.cta_destino_id.id or False,
            'cta_origen_id': self.cta_origen_id and self.cta_origen_id.id or False,
            'num_cheque': self.num_cheque or '',
            'benef_id': self.benef_id and self.benef_id.id or False,
            'metodo_pago_id': self.metodo_pago_id and self.metodo_pago_id.id or False,
            'tipo_pago': self.ttype or '',
            'formapago_id': payment_method,
            'invoice_ids': [(6, 0, invoice_ids.ids)],
            'name': self.move_name and self.move_name.replace("/", "")
        }
        if not payments.partner_id:
            partner_id = invoice_ids.mapped('partner_id')
            vals['partner_id'] = partner_id.id
        if self.partner_factoraje_id:
            vals['partner_factoraje_id'] = self.partner_factoraje_id.id
            vals['cfdi_factoraje_id'] = self.cfdi_factoraje_id.id
        payments.write(vals)
        payments.with_context(ctx_inv=ctx_inv).action_validate_cfdi()
        return move

    @api.multi
    def cfdi_is_required(self):
        self.ensure_one()
        if self.amount < 0:
            partner_type = 'supplier'
        else:
            partner_type = 'customer'
        required = (
            partner_type == "customer" and
            self.journal_id.id in self.env.user.company_id.cfd_mx_journal_ids.ids
        )
        if getattr(self, 'pos_statement_id', False):
            return False
        return required