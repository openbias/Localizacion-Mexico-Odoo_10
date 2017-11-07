# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

INCOTERM = [
    ('CFR', 'COSTE Y FLETE (PUERTO DE DESTINO CONVENIDO).'),
    ('CIF', 'COSTE, SEGURO Y FLETE (PUERTO DE DESTINO CONVENIDO).'),
    ('CPT', 'TRANSPORTE PAGADO HASTA (EL LUGAR DE DESTINO CONVENIDO).'),
    ('CIP', 'TRANSPORTE Y SEGURO PAGADOS HASTA (LUGAR DE DESTINO CONVENIDO).'),
    ('DAF', 'ENTREGADA EN FRONTERA (LUGAR CONVENIDO).'),
    ('DAP', 'ENTREGADA EN LUGAR.'),
    ('DAT', 'ENTREGADA EN TERMINAL.'),
    ('DES', 'ENTREGADA SOBRE BUQUE (PUERTO DE DESTINO CONVENIDO).'),
    ('DEQ', 'ENTREGADA EN MUELLE (PUERTO DE DESTINO CONVENIDO).'),
    ('DDU', 'ENTREGADA DERECHOS NO PAGADOS (LUGAR DE DESTINO CONVENIDO).'),
    ('DDP', 'ENTREGADA DERECHOS PAGADOS (LUGAR DE DESTINO CONVENIDO).'),
    ('EXW', 'EN FABRICA (LUGAR CONVENIDO).'),
    ('FCA', 'FRANCO TRANSPORTISTA (LUGAR DESIGNADO).'),
    ('FAS', 'FRANCO AL COSTADO DEL BUQUE (PUERTO DE CARGA CONVENIDO).'),
    ('FOB', 'FRANCO A BORDO (PUERTO DE CARGA CONVENIDO).')
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

class ResPartner(models.Model):
    _inherit = "res.partner"

    municipio_id = fields.Many2one('res.country.state.municipio', string='Municipio', required=False)


class addendas(models.Model):
    _inherit = 'cfd_mx.conf_addenda'

    model_selection = fields.Selection(selection_add=[('complemento_comercio_exterior', 'Complemento Comercio Exterior')])


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    comercio_exterior_tipo_operacion = fields.Selection([
            ('A','Exportación de servicios'),
            ('2','Exportación')
        ], string=u"Tipo de opración")
    comercio_exterior_clave_pedimento = fields.Selection([
            ('A1', 'IMPORTACION O EXPORTACION DEFINITIVA')
        ], string="Clave de pedimento")
    comercio_exterior_certificado_origen = fields.Selection([
            ('0','No funge como certificado de origen'),
            ('1','Funge como certificado de origen')
        ], string="Certificado origen")
    comercio_exterior_num_certificado_origen = fields.Char(string="Folio certificado origen", size=40, 
        help="""Atributo opcional para expresar el folio del certificado de origen 
            o el folio fiscal del CFDI con el que se pagó la expedición del certificado de origen""")
    comercio_exterior_num_exportador_confiable = fields.Char(string=u"Número de exportador confiable", size=50, 
        help="""Atributo opcional que indica el número de exportador confiable, 
        conforme al artículo 22 del Anexo 1 del Tratado de Libre Comercio con la Asociación Europea y a la Decisión de la Comunidad Europea.""")
    comercio_exterior_incoterm = fields.Selection(INCOTERM, string="INCOTERM")
    comercio_exterior_subdivision = fields.Selection([
        ('0','No'), ('1','Sí')], string=u"La factura tiene subdivisión")
    comercio_exterior_observaciones = fields.Char(string="Observaciones", size=300)
    comercio_exterior_tipo_cambio_usd = fields.Float(string="Tipo cambio USD")
    comercio_exterior_total_usd = fields.Float(string="Total USD")

    #Emisor
    comercio_exterior_curp_emisor = fields.Char(string="CURP", size=18, 
        help="""Atributo opcional para expresar la CURP del emisor del CFDI cuando es una persona física""")

    #Receptor
    comercio_exterior_curp_receptor = fields.Char(string="CURP", size=18, 
        help=""""Atributo opcional para expresar la CURP del receptor del CFDI cuando es una persona física""")
    comercio_exterior_numregidtrib_receptor = fields.Char(string="Num. de Identificación", size=40, 
        help="""Atributo requerido para incorporar el número de identificación o registro fiscal del país de residencia para efectos fiscales del receptor del CFDI.""")

    #Destinatario
    comercio_exterior_numregidtrib_destinatario = fields.Char(string="Num. de Identificación", size=40, 
        help="""Atributo opcional para incorporar el número de identificación o registro fiscal del país de residencia para efectos fiscales del destinatario de la mercancía exportada.""")
    comercio_exterior_rfc_destinatario = fields.Char(string="RFC", size=13, 
        help="""Atributo opcional para expresar el RFC del destinatario de la mercancía exportada.""")
    comercio_exterior_curp_destinatario = fields.Char(string="CURP", size=18, 
        help="""Atributo opcional para expresar la CURP del destinatario de la mercancía cuando es persona física""")
    comercio_exterior_nombre_destinatario = fields.Char(string="Nombre", 
        help="""Atributo opcional para expresar el nombre completo, denominación o razón social del destinatario de la mercancía exportada.""")
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
        conf_addenda_id = conf_addenda.search([('model_selection','=', 'complemento_comercio_exterior')])
        if conf_addenda_id:
            res = self.partner_id.id in conf_addenda_id.partner_ids.ids
            self.comercio_exterior_activate = res


    @api.multi
    def update_comercio_exterior_lines(self):
        comercio_exterior_obj = self.env['comercio_exterior']
        for record in self:
            for line in record.invoice_line_ids:
                for comercio_exterior_line in record.comercio_exterior_line_ids:
                    if comercio_exterior_line.invoice_line_id.id == line.id:
                        break
                else:
                    comercio_exterior_obj.create({
                        'invoice_line_id': line.id,
                        'invoice_id': record.id
                    })
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
    
    comercio_exterior_no_identificacion = fields.Char(string=u'Número de indentifación', size=100)
    comercio_exterior_fraccion_arancelaria = fields.Char(string=u'Fraccion Arancelaria')
    comercio_exterior_cantidad_aduana = fields.Float(string=u'Cantidad aduana', help="""Atributo opcional para precisar la cantidad de bienes en la
            aduana conforme a la UnidadAduana cuando en el nodo Comprobante:Conceptos:Concepto se hubiera registrado información comercial.""")
    comercio_exterior_unidad_aduana = fields.Selection(UNIDAD_MEDIDA, string="Unidad de medida")
    comercio_exterior_valor_aduana = fields.Float(string="Valor unitario aduana", help="""Atributo opcional para precisar el valor o precio unitario del bien en la aduana. Se expresa en dólares de Estados Unidos (USD).""")
    comercio_exterior_valor_dolares = fields.Float(u"Valor en dólares")
    comercio_exterior_descripciones_especificas = fields.One2many("comercio_exterior.desc_esp", 'invoice_line_id', string=u"Descripciones Específicas")
    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one("account.invoice.line", readonly=True, string="Linea de la factura")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
