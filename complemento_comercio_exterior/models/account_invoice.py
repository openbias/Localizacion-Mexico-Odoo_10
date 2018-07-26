# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import collections
import logging

logging.basicConfig(level=logging.INFO)

INCOTERM = [
    ('CFR', '[CFR] COSTE Y FLETE (PUERTO DE DESTINO CONVENIDO).'),
    ('CIF', '[CIF] COSTE, SEGURO Y FLETE (PUERTO DE DESTINO CONVENIDO).'),
    ('CPT', '[CPT] TRANSPORTE PAGADO HASTA (EL LUGAR DE DESTINO CONVENIDO).'),
    ('CIP', '[CIP] TRANSPORTE Y SEGURO PAGADOS HASTA (LUGAR DE DESTINO CONVENIDO).'),
    ('DAF', '[DAF] ENTREGADA EN FRONTERA (LUGAR CONVENIDO).'),
    ('DAP', '[DAP] ENTREGADA EN LUGAR.'),
    ('DAT', '[DAT] ENTREGADA EN TERMINAL.'),
    ('DES', '[DES] ENTREGADA SOBRE BUQUE (PUERTO DE DESTINO CONVENIDO).'),
    ('DEQ', '[DEQ] ENTREGADA EN MUELLE (PUERTO DE DESTINO CONVENIDO).'),
    ('DDU', '[DDU] ENTREGADA DERECHOS NO PAGADOS (LUGAR DE DESTINO CONVENIDO).'),
    ('DDP', '[DDP] ENTREGADA DERECHOS PAGADOS (LUGAR DE DESTINO CONVENIDO).'),
    ('EXW', '[EXW] EN FABRICA (LUGAR CONVENIDO).'),
    ('FCA', '[FCA] FRANCO TRANSPORTISTA (LUGAR DESIGNADO).'),
    ('FAS', '[FAS] FRANCO AL COSTADO DEL BUQUE (PUERTO DE CARGA CONVENIDO).'),
    ('FOB', '[FOB] FRANCO A BORDO (PUERTO DE CARGA CONVENIDO).')
]

UNIDAD_MEDIDA = [
    ('1', 'KILO'),
    ('2', 'GRAMO'),
    ('3', 'METRO LINEAL'),
    ('4', 'METRO CUADRADO'),
    ('5', 'METRO CUBICO'),
    ('6', 'PIEZA'),
    ('7', 'CABEZA'),
    ('8', 'LITRO'),
    ('9', 'PAR'),
    ('10', 'KILOWATT'),
    ('11', 'MILLAR'),
    ('12', 'JUEGO'),
    ('13', 'KILOWATT/HORA'),
    ('14', 'TONELADA'),
    ('15', 'BARRIL'),
    ('16', 'GRAMO NETO'),
    ('17', 'DECENAS'),
    ('18', 'CIENTOS'),
    ('19', 'DOCENAS'),
    ('20', 'CAJA'),
    ('21', 'BOTELLA'),
    ('99', 'NA')
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fraccion_arancelaria_id = fields.Many2one('comercio_exterior.fraccionarancelaria', string='Fraccion Arancelaria', required=False)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    def _compute_comercio_exterior_activate(self):
        conf_addenda = self.env['cfd_mx.conf_addenda']
        conf_addenda_id = conf_addenda.search([('model_selection','=', 'complemento_comercio_exterior')])
        if conf_addenda_id:
            res = self.id in conf_addenda_id.partner_ids.ids
            self.comercio_exterior_activate = res

    @api.one
    def _compute_esmex(self):
        if self.country_id:
            mx_id = self.env.ref('base.mx')
            if mx_id == self.country_id:
                self.es_mex = True
            else:
                self.es_mex = False

    comercio_exterior_referencia = fields.Char(string='Referencia', help="Se puede registrar una referencia geográfica adicional que permita una más fácil o precisa ubicación del domicilio del emisor del comprobante, por ejemplo cordenadas GPS.")
    municipio_id = fields.Many2one('res.country.state.municipio', string='Municipio', required=False)
    ciudad_id = fields.Many2one('res.country.state.ciudad', string='Ciudad', required=False)
    colonia_id = fields.Many2one('res.country.state.municipio.colonia', string='Colonia', required=False)
    codigo_postal_id = fields.Many2one('res.country.state.cp', string='Codigo Postal', required=False)
    comercio_exterior_activate = fields.Boolean("Activar", compute='_compute_comercio_exterior_activate')
    es_mex = fields.Boolean('Es MEX?', compute='_compute_esmex')

    @api.multi
    @api.onchange('codigo_postal_id')
    def onchange_codigo_postal_id(self):
        if not self.codigo_postal_id:
            return True
        self.municipio_id = self.codigo_postal_id.municipio_id
        self.ciudad_id = self.codigo_postal_id.ciudad_id


class addendas(models.Model):
    _inherit = 'cfd_mx.conf_addenda'

    model_selection = fields.Selection(selection_add=[('complemento_comercio_exterior', 'Complemento Comercio Exterior')])

    def complemento_comercio_exterior_create_addenda(self, invoice):
        context = self._context or {}

        comercio_attribs = {}
        comercio_attribs["Version"]= "1.1"
        comercio_attribs["TipoOperacion"]= '%s'%invoice.comercio_exterior_tipo_operacion
        comercio_attribs["ClaveDePedimento"]= '%s'%invoice.comercio_exterior_clave_pedimento
        comercio_attribs["CertificadoOrigen"]= '%s'%invoice.comercio_exterior_certificado_origen
        comercio_attribs["Incoterm"]= '%s'%invoice.comercio_exterior_incoterm
        comercio_attribs["Subdivision"]= '%s'%invoice.comercio_exterior_subdivision
        if invoice.comercio_exterior_num_exportador_confiable:
            comercio_attribs["NumeroExportadorConfiable"]= '%s'%invoice.comercio_exterior_num_exportador_confiable
        if invoice.comercio_exterior_certificado_origen != '0':
            comercio_attribs['NumCertificadoOrigen']= '%s'%invoice.comercio_exterior_num_certificado_origen
        if invoice.comercio_exterior_observaciones:
            comercio_attribs['Observaciones']= '%s'%invoice.comercio_exterior_observaciones
        if invoice.comercio_exterior_tipo_cambio_usd:
            comercio_attribs['TipoCambioUSD']= '%s'%invoice.comercio_exterior_tipo_cambio_usd
        if invoice.comercio_exterior_total_usd:
            comercio_attribs['TotalUSD']= '%.2f'%invoice.comercio_exterior_total_usd

        # Emisor
        partner_id = invoice.company_id.partner_id
        emisor_dom_attribs = {}
        emisor_dom_attribs['Calle']= '%s'%partner_id.street
        if partner_id.noExterior:
            emisor_dom_attribs['NumeroExterior']= '%s'%partner_id.noExterior
        if partner_id.noInterior:
            emisor_dom_attribs['NumeroInterior']= '%s'%partner_id.noInterior
        if partner_id.colonia_id:
            emisor_dom_attribs['Colonia']= '%s'%partner_id.colonia_id.clave_sat
        if partner_id.ciudad_id:
            emisor_dom_attribs['Localidad']= '%s'%partner_id.ciudad_id.clave_sat
        if partner_id.comercio_exterior_referencia:
            emisor_dom_attribs['Referencia']= '%s'%partner_id.comercio_exterior_referencia
        if partner_id.municipio_id:
            emisor_dom_attribs['Municipio']= '%s'%partner_id.municipio_id.clave_sat
        if partner_id.state_id:
            emisor_dom_attribs['Estado']= '%s'%partner_id.state_id.code
        if partner_id.country_id:
            emisor_dom_attribs['Pais']= '%s'%partner_id.country_id.code_alpha3
        if partner_id.codigo_postal_id:
            emisor_dom_attribs['CodigoPostal']= '%s'%partner_id.codigo_postal_id.name

        emisor_attribs = {}
        if invoice.partner_id.curp:
            emisor_attribs['Curp']= '%s'%invoice.partner_id.curp
        # emisor_attribs['Emisor'] = emisor_dom_attribs

        # Receptor
        partner_id = invoice.partner_id
        receptor_dom_attribs = {}
        receptor_dom_attribs['Calle']= '%s'%partner_id.street
        if partner_id.noExterior:
            receptor_dom_attribs['NumeroExterior']= '%s'%partner_id.noExterior
        if partner_id.noInterior:
            receptor_dom_attribs['NumeroInterior']= '%s'%partner_id.noInterior
        if partner_id.es_mex:
            if partner_id.colonia_id:
                receptor_dom_attribs['Colonia']= '%s'%partner_id.colonia_id.clave_sat
            if partner_id.ciudad_id:
                receptor_dom_attribs['Localidad']= '%s'%partner_id.ciudad_id.clave_sat
            if partner_id.municipio_id:
                receptor_dom_attribs['Municipio']= '%s'%partner_id.municipio_id.clave_sat
            if partner_id.codigo_postal_id:
                receptor_dom_attribs['CodigoPostal']= '%s'%partner_id.codigo_postal_id.name
        else:
            if partner_id.street2:
                receptor_dom_attribs['Colonia']= '%s'%partner_id.street2
            if partner_id.city:
                receptor_dom_attribs['Localidad']= '%s'%partner_id.city
            if partner_id.zip:
                receptor_dom_attribs['CodigoPostal']= '%s'%partner_id.zip
        if partner_id.comercio_exterior_referencia:
            receptor_dom_attribs['Referencia']= '%s'%partner_id.comercio_exterior_referencia
        if partner_id.state_id:
            receptor_dom_attribs['Estado']= '%s'%partner_id.state_id.code
        if partner_id.country_id:
            receptor_dom_attribs['Pais']= '%s'%partner_id.country_id.code_alpha3

        destinatario_attribs = {}
        destinatario_dom_attribs = {}
        if invoice.comercio_exterior_domicilio_destinatario:
            partner_id = invoice.comercio_exterior_domicilio_destinatario
            destinatario_attribs['Nombre']= '%s'%partner_id.name
            if partner_id.identidad_fiscal:
                destinatario_attribs['NumRegIdTrib']= '%s'%partner_id.identidad_fiscal
            
            destinatario_dom_attribs['Calle']= '%s'%partner_id.street
            if partner_id.noExterior:
                destinatario_dom_attribs['NumeroExterior']= '%s'%partner_id.noExterior
            if partner_id.noInterior:
                destinatario_dom_attribs['NumeroInterior']= '%s'%partner_id.noInterior
            if partner_id.es_mex:
                if partner_id.colonia_id:
                    destinatario_dom_attribs['Colonia']= '%s'%partner_id.colonia_id.clave_sat
                if partner_id.ciudad_id:
                    destinatario_dom_attribs['Localidad']= '%s'%partner_id.ciudad_id.clave_sat
                if partner_id.municipio_id:
                    destinatario_dom_attribs['Municipio']= '%s'%partner_id.municipio_id.clave_sat
                if partner_id.codigo_postal_id:
                    destinatario_dom_attribs['CodigoPostal']= '%s'%partner_id.codigo_postal_id.name
            else:
                if partner_id.street2:
                    destinatario_dom_attribs['Colonia']= '%s'%partner_id.street2
                if partner_id.city:
                    destinatario_dom_attribs['Localidad']= '%s'%partner_id.city
                if partner_id.zip:
                    destinatario_dom_attribs['CodigoPostal']= '%s'%partner_id.zip
            if partner_id.comercio_exterior_referencia:
                destinatario_dom_attribs['Referencia']= '%s'%partner_id.comercio_exterior_referencia
            if partner_id.state_id:
                destinatario_dom_attribs['Estado']= '%s'%partner_id.state_id.code
            if partner_id.country_id:
                destinatario_dom_attribs['Pais']= '%s'%partner_id.country_id.code_alpha3

        mercancias = []
        for line in invoice.comercio_exterior_line_ids:
            mercancias_attribs = {
                'NoIdentificacion': '%s'%line.comercio_exterior_no_identificacion,
                'FraccionArancelaria': '%s'%line.comercio_exterior_fraccion_arancelaria_id.clave,
                'CantidadAduana': '%s'%line.comercio_exterior_cantidad_aduana,
                'UnidadAduana': '%s'%line.comercio_exterior_unidad_aduana_id.clave,
                'ValorUnitarioAduana': '%s'%line.comercio_exterior_valor_aduana,
                'ValorDolares': '%.2f'%line.comercio_exterior_valor_dolares
            }
            desc_esp_attribs = []
            for dline in line.comercio_exterior_descripciones_especificas:
                d = {
                    'Marca': '%s'%dline.marca,
                    'Modelo': '%s'%dline.modelo,
                    'SubModelo': '%s'%dline.submodelo,
                    'NumeroSerie': '%s'%dline.numero_serie
                }
                desc_esp_attribs.append(d)


            mercancias.append({
                    line.id: {
                        'mercancias_attribs': mercancias_attribs,
                        'desc_esp_attribs': desc_esp_attribs
                    }
                })

        dict_addenda = {
            'type': 'Complemento',
            'name': self.model_selection,
            'addenda':{
                'comercio_attribs': comercio_attribs,
                'Emisor': {
                    'emisor_attribs': emisor_attribs,
                    'emisor_dom_attribs': emisor_dom_attribs
                },
                'Receptor': {
                    'receptor_dom_attribs': receptor_dom_attribs
                },
                'Destinatario': {
                    'destinatario_attribs': destinatario_attribs,
                    'destinatario_dom_attribs': destinatario_dom_attribs,
                },
                'Mercancias': mercancias
            }
        }
        return dict_addenda


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    comercio_exterior_tipo_operacion = fields.Selection([
            ('A','[A] Exportación de servicios'),
            ('2','[2] Exportación')
        ], string=u"Tipo de opración")
    comercio_exterior_clave_pedimento = fields.Selection([
            ('A1', '[A1] IMPORTACION O EXPORTACION DEFINITIVA')
        ], string="Clave de pedimento")
    comercio_exterior_certificado_origen = fields.Selection([
            ('0','[0] No funge como certificado de origen'),
            ('1','[1] Funge como certificado de origen')
        ], string="Certificado origen")
    comercio_exterior_num_certificado_origen = fields.Char(string="Folio certificado origen", size=40, 
        help="""Atributo opcional para expresar el folio del certificado de origen 
            o el folio fiscal del CFDI con el que se pagó la expedición del certificado de origen""")
    comercio_exterior_num_exportador_confiable = fields.Char(string=u"Número de exportador confiable", size=50, 
        help="""Atributo opcional que indica el número de exportador confiable, 
        conforme al artículo 22 del Anexo 1 del Tratado de Libre Comercio con la Asociación Europea y a la Decisión de la Comunidad Europea.""")
    comercio_exterior_incoterm = fields.Selection(INCOTERM, string="INCOTERM")
    comercio_exterior_subdivision = fields.Selection([
        ('0','[0] No'), ('1','[1] Sí')], string=u"La factura tiene subdivisión")
    comercio_exterior_observaciones = fields.Char(string="Observaciones", size=300)
    comercio_exterior_tipo_cambio_usd = fields.Float(string="Tipo cambio USD", digits=(12, 6))
    comercio_exterior_total_usd = fields.Float(string="Total USD")
    comercio_exterior_domicilio_destinatario = fields.Many2one('res.partner', string="Domicilio del destinatario")
    comercio_exterior_activate = fields.Boolean("Activar")
    comercio_exterior_line_ids = fields.One2many('comercio_exterior', 'invoice_id')

    @api.model
    def create(self, vals):
        onchanges = {
            'onchange_activatecomercio': ['partner_id'],
        }
        for onchange_method, changed_fields in onchanges.items():
            if any(f not in vals for f in changed_fields):
                invoice = self.new(vals)
                getattr(invoice, onchange_method)()
                for field in changed_fields:
                    if field not in vals and invoice[field]:
                        vals[field] = invoice._fields[field].convert_to_write(invoice[field], invoice)
        invoice = super(AccountInvoice, self).create(vals)
        return invoice

    @api.multi
    @api.onchange('partner_id')
    def onchange_activatecomercio(self):
        if not self.partner_id:
            self.update({
                'comercio_exterior_activate': False,
            })
            return

        conf_addenda = self.env['cfd_mx.conf_addenda']
        conf_addenda_id = conf_addenda.search([('model_selection','=', 'complemento_comercio_exterior'), ('company_id', '=', self.company_id.id)])
        if conf_addenda_id:
            res = self.partner_id.id in conf_addenda_id.partner_ids.ids
            self.comercio_exterior_activate = res

    @api.multi
    def update_comercio_exterior_lines(self):
        comercio_exterior_obj = self.env['comercio_exterior']
        for record in self:
            for line in record.invoice_line_ids:
                fra_id = line.product_id.fraccion_arancelaria_id or False
                vals = {
                    'comercio_exterior_no_identificacion': line.product_id.default_code or '',
                    'comercio_exterior_fraccion_arancelaria_id': fra_id and fra_id.id or '',
                    'invoice_line_id': line.id,
                    'invoice_id': record.id,
                    'comercio_exterior_cantidad_aduana': line.quantity
                }
                if fra_id:
                    vals['comercio_exterior_unidad_aduana_id'] = fra_id and fra_id.unidadaduana_id and fra_id.unidadaduana_id.id or False
                if len(record.comercio_exterior_line_ids) == 0:
                    comercio_exterior_obj.create(vals)
                for comercio_exterior_line in record.comercio_exterior_line_ids:
                    if comercio_exterior_line.invoice_line_id.id == line.id:
                            comercio_exterior_line.write(vals)
                    else:
                        comercio_exterior_obj.create(vals)
        return True




class DescripcionesEspecificas(models.Model):
    _name = "comercio_exterior.desc_esp"

    marca = fields.Char(string='Marca', size=35, required=True)
    modelo = fields.Char(string='Modelo', size=80)
    submodelo = fields.Char(string='Submodelo', size=50)
    numero_serie = fields.Char(string='Número de Serie', size=40)
    invoice_line_id = fields.Many2one("comercio_exterior", string=u"Línea de la mercancia")


class ComercioExterior(models.Model):
    _name = "comercio_exterior"

    comercio_exterior_fraccion_arancelaria_id = fields.Many2one('comercio_exterior.fraccionarancelaria', string='Fraccion Arancelaria')
    comercio_exterior_unidad_aduana_id = fields.Many2one('comercio_exterior.unidadaduana', string='Unidad Aduana')

    comercio_exterior_no_identificacion = fields.Char(string=u'Número de indentifación', size=100)
    comercio_exterior_cantidad_aduana = fields.Float(string=u'Cantidad aduana', help="""Atributo opcional para precisar la cantidad de bienes en la
            aduana conforme a la UnidadAduana cuando en el nodo Comprobante:Conceptos:Concepto se hubiera registrado información comercial.""")
    comercio_exterior_valor_aduana = fields.Float(string="Valor unitario aduana", help="""Atributo opcional para precisar el valor o precio unitario del bien en la aduana. Se expresa en dólares de Estados Unidos (USD).""")
    comercio_exterior_valor_dolares = fields.Float(u"Valor en dólares")
    comercio_exterior_descripciones_especificas = fields.One2many("comercio_exterior.desc_esp", 'invoice_line_id', string=u"Descripciones Específicas")
    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one("account.invoice.line", readonly=True, string="Linea de la factura")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
