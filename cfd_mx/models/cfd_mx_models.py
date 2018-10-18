# -*- coding: utf-8 -*-

from xml.dom import minidom
from xml.dom.minidom import parse, parseString
import json, base64, urllib
import csv
import os
import inspect

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.addons.bias_base_report.bias_utis.amount_to_text_es_MX import amount_to_text

import logging
logging.basicConfig(level=logging.INFO)

def extraeDecimales(nNumero, max_digits=2):
    strDecimales = str( round(nNumero%1, 2) ).replace('0.','')
    strDecimales += "0"*max_digits
    strDecimales = strDecimales[0:max_digits]
    return long( strDecimales )

def cant_letra(currency, amount):
    if currency.name == 'COP':
        nombre = currency.nombre_largo or 'M/CTE'
        siglas = 'M/CTE'
        nNumero = round( amount , 2)
        decimales = extraeDecimales(nNumero, 2)
        am = str(nNumero).split('.')
        n_entero = amount_to_text().amount_to_text_cheque(float(am[0]), nombre, "").replace("  ", "").replace("00/100", "")
        n_decimales = amount_to_text().amount_to_text_cheque(float(decimales), 'centavos', siglas).replace("00/100 ", "")
        name = "%s con %s "%(n_entero, n_decimales)
    else:
        nombre = currency.nombre_largo or ''
        siglas = currency.name
        name = amount_to_text().amount_to_text_cheque(float(amount), nombre, siglas).capitalize()
    return name

class CFDITimbresSat(models.Model):
    _name = 'cfdi.timbres.sat'
    _inherit = ['mail.thread']
    _description = 'CFDI Timbres'
    _order = "time_invoice desc, name desc, id desc"

    name = fields.Char('Fiscal Folio', copy=False, readonly=True, help='Folio in electronic invoice, is returned by SAT when send to stamp')
    cfdi_supplier_rfc = fields.Char(string='Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.')
    cfdi_customer_rfc = fields.Char(string='Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.')
    cfdi_pac_rfc = fields.Char(string='PAC RFC', copy=False, readonly=True,
        help='The PAC tax identification number.')
    cfdi_amount = fields.Monetary(string='Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.')
    cfdi_certificate = fields.Char(string='Certificate', copy=False, readonly=True,
        help='The certificate used during the generation of the cfdi.')
    cfdi_certificate_sat = fields.Char(string='Certificate SAT', copy=False, readonly=True,
        help='The certificate of the SAT used during the generation of the cfdi.')
    time_invoice = fields.Char(
        string='Time invoice', readonly=True, copy=False,
        help="Keep empty to use the current México central time")
    time_invoice_sat = fields.Char(
        string='Time invoice SAT', readonly=True, copy=False,
        help="Refers to the time of stamp of SAT")
    cfdi_cancel_date_sat = fields.Char(
        string='Date Cancel SAT', readonly=True, copy=False,
        help="Refers to the date of cancellation of the CFDI Invoice.")
    cfdi_cancel_status_sat = fields.Char(
        string='Status Cancel SAT', readonly=True, copy=False,
        help="Refers to the status of cancellation of the CFDI Invoice.")
    cfdi_cancel_code_sat = fields.Char(
        string='Code Cancel SAT', readonly=True, copy=False,
        help="Refers to the code of cancellation of the CFDI Invoice.")
    cfdi_cadena_ori = fields.Text(string="Cadena", copy=False)
    cfdi_cadena_sat = fields.Text(string="Cadena SAT", copy=False)
    cfdi_qrcode = fields.Binary(string="Codigo QR", copy=False)

    journal_id = fields.Many2one('account.journal', string=u'Journal')
    partner_id = fields.Many2one('res.partner', string=u'Partner')
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True,  
        track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, default=lambda self: self.env['res.company']._company_default_get('cfdi.timbres.sat'))
    cfdi_type = fields.Selection(
        selection=[
            ('I', 'Ingreso'),
            ('E', 'Egreso'),
            ('T', 'Traslado'),
            ('P', 'Pagos'),
            ('N', 'Nomina'),
        ],
        string='Type CFDI',
        help='Refers to the type of the invoice inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined')
    cfdi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        string='SAT status',
        help='Refers to the status of the invoice inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined')


    @api.multi
    def get_xml_cfdi(self):
        nodosPagos = []
        timbreAtrib = {}
        compAtrib = {}
        receptorAtrib = {}
        emisorAtrib = {}
        att_obj = self.env['ir.attachment']
        for rec in self:
            att_ids = att_obj.search([('res_model', '=', 'cfdi.timbres.sat'), ('res_id', '=', rec.id), ('type', '=', 'binary'), ('name', 'ilike', '%s.xml'%(rec.name) )])
            for att_id in att_ids:
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
            'timbreAtrib': timbreAtrib
        }


    @api.multi
    def get_total_cfdi(self, uuid):
        inv_id = self.env['account.invoice'].search([('uuid', '=', uuid)], limit=1)
        return inv_id and inv_id.amount_total or 0.0

    @api.multi
    def getCantLetra(self):
        self.ensure_one()
        return "MXN"

    @api.multi
    def getFormaPago(self, formapago):
        forma = self.env["cfd_mx.formapago"].search([('clave', '=', formapago)], limit=1)
        if forma:
            return "%s - %s"%(forma.clave, forma.name)
        return formapago

    @api.multi
    def cfdi_amount_to_text(self, moneda, amount_total):
        self.ensure_one()
        currency_id = self.env['res.currency'].search([('name', '=', moneda)], limit=1)
        cantLetra = cant_letra(currency_id, amount_total) or ''
        return cantLetra.upper()

    @api.multi
    def getUrlQR(self, sello):
        self.ensure_one()
        args = {
            'id': self.name, 're': self.cfdi_supplier_rfc, 'rr': self.cfdi_customer_rfc, 'tt': self.cfdi_amount, 'fe': str(sello[-10:]).replace("=","")
        }
        url = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id={id}&re={re}&rr={rr}&tt={tt}&fe={fe}".format(**args)
        return urllib.pathname2url(url)


class AltaCatalogosCFDI(models.TransientModel):
    _name = 'cf.mx.alta.catalogos.wizard'
    _description = 'Alta Catalogos CFDI'

    @api.multi
    def action_alta_catalogos(self):
        logging.info(' Inicia Alta Catalogos')
        models = [
            'comercio_exterior.unidadaduana',
            'comercio_exterior.fraccionarancelaria',
            'cfd_mx.unidadesmedida',
            'cfd_mx.prodserv',
            'res.country.state.ciudad',
            'res.country.state.municipio',
            'res.country.state.cp',
            'res.country.state.municipio.colonia'
        ]
        for model in models:
            model_name = model.replace('.', '_')
            logging.info(' Model: -- %s'%model_name )
            model_obj = self.env[model]
            fname = '/../data/json/%s.json' % model
            current_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            path =  current_path+fname
            jdatas = json.load(open(path))
            for indx, data in enumerate(jdatas):
                header = data.keys()
                body = data.values()
                r = model_obj.with_context(noupdate=True).load(header, [body])
                logging.info(' Model: -- %s, Res: %s - %s'%(model_name, indx, r) )
                if r.get("messages"):
                    logging.info(' Model: -- %s, Res: %s - %s'%(model_name, indx, r) )
                self._cr.commit()
        return True


class TipoRelacion(models.Model):
    _name = "cfd_mx.tiporelacion"

    name = fields.Char("Descripcion", size=128)
    clave = fields.Char(string="Clave", help="Clave Tipo Relacion")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoRelacion, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class UsoCfdi(models.Model):
    _name = "cfd_mx.usocfdi"

    name = fields.Char("Descripcion", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(UsoCfdi, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class MetodoPago(models.Model):
    _name = "cfd_mx.metodopago"

    name = fields.Char("Descripcion", size=128, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(MetodoPago, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class Regimen(models.Model):
    _name = "cfd_mx.regimen"

    name = fields.Char("Regimen Fiscal", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    persona_fisica = fields.Boolean(string="Aplica Persona Fisica")
    persona_moral = fields.Boolean(string="Aplica Persona Moral")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(Regimen, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class FormaPago(models.Model):
    _name = 'cfd_mx.formapago'

    name = fields.Char(string="Descripcion", size=64, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    nombre_banco_ext = fields.Boolean(string="Nombre Banco", help="Nombre del Banco emisor de la cuenta ordenante en caso de extranjero")
    banco = fields.Boolean(string="Banco", help="Activar este checkbox para que pregunte número de cuenta")
    no_operacion = fields.Boolean(string="Num. Operacion", default=False)
    rfc_ordenante = fields.Boolean(string="RFC Ordenante", default=False)
    cuenta_ordenante = fields.Boolean(string="Cuenta Ordenante", default=False)
    patron_ordenante = fields.Char(string="Patron Ordenante", default='')
    rfc_beneficiario = fields.Boolean(string="RFC Beneficiario", default=False)
    cuenta_beneficiario = fields.Boolean(string="Cuenta Beneficiario", default=False)
    patron_beneficiario = fields.Char(string="Patron Beneficiario", default='')
    tipo_cadena = fields.Boolean(string="Tipo Cadena", default=False)
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    pos_metodo = fields.Many2one('account.journal', domain=[('journal_user', '=', 1)],
            string="Metodo de pago del TPV")
    conta_elect = fields.Boolean("Es Contabilidad Electronica?", default=False)


    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class ClaveProdServ(models.Model):
    _name = 'cfd_mx.prodserv'
    _description = 'Clave del Producto o Servicio'

    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    name = fields.Char("Descripcion", size=264, required=True, default="")
    incluir_iva = fields.Char(string='Incluir IVA trasladado')
    incluir_ieps = fields.Char(string='Incluir IVA trasladado')
    complemento = fields.Char("Complemento Incluir", required=False, default="")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    similares = fields.Char("Palabras Similares", required=False, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class UnidadesMedida(models.Model):
    _name = 'cfd_mx.unidadesmedida'
    _description = u"Catalogo de unidades de medida para los conceptos en el CFDI."

    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    name = fields.Char(string="Nombre", size=264, required=True, default="")
    descripcion = fields.Char("Descripcion", required=False, default="")
    nota = fields.Char("Nota", required=False, default="")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    simbolo = fields.Char("Simbolo", required=False, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class Aduana(models.Model):
    _name = "cfd_mx.aduana"

    name = fields.Char("Regimen Fiscal", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(Aduana, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class Addendas(models.Model):
    _name = 'cfd_mx.conf_addenda'

    name = fields.Char("Name")
    model_selection = fields.Selection(selection=[])
    partner_ids = fields.Many2many('res.partner', string="Clientes", domain=[('customer', '=', True )] )
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=False,  default=lambda self: self.env['res.company']._company_default_get('cfd_mx.conf_addenda'))

    def create_addenda(self, invoices):
        context = self._context or {}
        cfd_addenda = self.model_selection
        if hasattr(self, '%s_create_addenda' % cfd_addenda):
            return getattr(self, '%s_create_addenda' % cfd_addenda)(invoices)
        else:
            raise ValidationError('La Addenda/Complemento "%s" no esta implementado'%(cfd_addenda))
            return False
        return True


#
# Comercio Exterior
#
class UnidadAduana(models.Model):
    _name = 'comercio_exterior.unidadaduana'

    name = fields.Char(string='Descripcion')
    clave = fields.Char(string='Clave SAT')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class FraccionArancelaria(models.Model):
    _name = 'comercio_exterior.fraccionarancelaria'

    name = fields.Char(string='Descripcion')
    clave = fields.Char(string='Clave SAT')
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    unidadaduana_id = fields.Many2one('comercio_exterior.unidadaduana', string='Unidad Aduana')


    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(FraccionArancelaria, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


########################################
#
# Quitar en Futuras versiones
#
########################################
class TipoPago(models.Model):
    _name = "cfd_mx.tipopago"

    name = fields.Char("Descripcion", size=128, required=True, default="")

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    aprobacion_ids = fields.One2many("cfd_mx.aprobacion", 'sequence_id', string='Aprobaciones')

class Aprobacion(models.Model):
    _name = 'cfd_mx.aprobacion'

    anoAprobacion = fields.Integer(string="Año de aprobación", required=True)
    noAprobacion = fields.Char(string="No. de aprobación", required=True)
    serie = fields.Char(string="Serie", size=8)
    del_field = fields.Integer(string="Del", required=True, oldname='del')
    al = fields.Integer(string="Al", required=True)
    sequence_id = fields.Many2one("ir.sequence", string="Secuencia", required=True)

class certificate(models.Model):
    _name = 'cfd_mx.certificate'

    serial = fields.Char(string="Número de serie", size=64, required=True)
    cer = fields.Binary(string='Certificado', filters='*.cer,*.certificate,*.cert', required=True)
    key = fields.Binary(string='Llave privada', filters='*.key', required=True)
    key_password = fields.Char('Password llave', size=64, invisible=False, required=True)
    cer_pem = fields.Binary(string='Certificado formato PEM', filters='*.pem,*.cer,*.certificate,*.cert')
    key_pem = fields.Binary(string='Llave formato PEM', filters='*.pem,*.key')
    pfx = fields.Binary(string='Archivo PFX', filters='*.pfx')
    pfx_password = fields.Char(string='Password archivo PFX', size=64, invisible=False)
    start_date = fields.Date(string='Fecha inicio', required=False)
    end_date = fields.Date(string='Fecha expiración', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', 
            required=True, default=lambda self: self.env.user.company_id.id)
    active = fields.Boolean(default=True, help="If the active field is set to False, it will allow you to hide the certificate without removing it.")

########################################
#
# Quitar en Futuras versiones
#
########################################