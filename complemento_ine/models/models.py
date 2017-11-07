# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


claves_entidades = ['AGU','BCN','BCS','CAM','CHP','CHH','COA','COL','DIF','DUR','GUA','GRO','HID','JAL','MEX','MIC','MOR','NAY','NLE','OAX','PUE','QTO','ROO','SLP','SIN','SON','TAB','TAM','TLA','VER','YUC','ZAC'] 

class addendas(models.Model):
    _inherit = 'cfd_mx.conf_addenda'

    model_selection = fields.Selection(selection_add=[('complemento_ine', 'Complemento INE')])

    def complemento_ine_create_addenda(self, invoice):
        tipo_proceso = {
            'ordinario': u'Ordinario',
            'precampanha': u'Precampaña',
            'campanha': u'Campaña'
        }
        tipo_comite = {
            'ejecutivo_nacional': 'Ejecutivo Nacional',
            'ejecutivo_estatal': 'Ejecutivo Estatal'
        }
        ine_tipo_proceso = tipo_proceso.get(invoice.ine_tipo_proceso, '')
        ine_tipo_comite = tipo_comite.get(invoice.ine_tipo_comite, '')
        ine_attribs = {
            'TipoProceso': ine_tipo_proceso,
            'TipoComite': ine_tipo_comite,
        }
        entidad_attribs = []
        if ine_tipo_proceso == 'Ordinario' and ine_tipo_comite == 'Ejecutivo Nacional':
            if not invoice.ine_id_contabilidad:
                raise UserError(u"Datos incompletos: \n\n Para el tipo de proceso Ordinario con comité ejecutivo nacional es necesario especificar el ID de contabilidad")
            if invoice.ine_id_contabilidad:
                ine_attribs['IdContabilidad'] = str(invoice.ine_id_contabilidad)
        for entidad in invoice.ine_entidades:
            nodo_entidad = {'ClaveEntidad': entidad.state_id.code}
            if ine_tipo_proceso != 'Ordinario':
                if entidad.ambito:
                    nodo_entidad["Ambito"] = entidad.ambito
            conta = []
            for contabilidad in entidad.contabilidad:
                conta.append({'IdContabilidad': str(contabilidad.id_contabilidad)})
            # nodo_entidad['contabilidad'] = conta
            entidad_attribs.append({
                    'entidad': nodo_entidad,
                    'contabilidad': conta
                })
                
        dict_addenda = {
            'type': 'Complemento',
            'name': self.model_selection,
            'addenda':{
                'ine_attribs': ine_attribs,
                'entidad_attribs': entidad_attribs,
            }
        }
        return dict_addenda
    

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    ine_activate = fields.Boolean("Activar complemento INE")
    ine_tipo_proceso = fields.Selection([
            ('ordinario', 'Ordinario'),
            ('precampanha', 'Precampaña'),
            ('campanha', 'Campaña')],
        string="Tipo de Proceso", required=False)
    ine_tipo_comite = fields.Selection([
            ('ejecutivo_nacional', 'Ejecutivo Nacional'),
            ('ejecutivo_estatal', 'Ejecutivo Estatal')],
        string=u"Tipo de comité", required=False)
    ine_id_contabilidad = fields.Integer("Id Contabilidad", 
            help="""Atributo para registrar la clave de contabilidad de aspirantes,
                precandidatos y concentradoras, si se trata de un tipo de proceso ordinario y un comité ejecutivo nacional. Para los otros casos,
                la clave de contabilidad se registra en la Entidad""")
    ine_entidades = fields.One2many("account.invoice.ine.entidad", "invoice_id", string="Entidades")

    @api.model
    def create(self, vals):
        onchanges = {
            'onchange_activateine': ['partner_id'],
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
    def onchange_activateine(self):
        if not self.partner_id:
            self.update({
                'ine_activate': False,
            })
            return

        conf_addenda = self.env['cfd_mx.conf_addenda']
        conf_addenda_id = conf_addenda.search([('model_selection','=', 'complemento_ine')])
        if conf_addenda_id:
            res = self.partner_id.id in conf_addenda_id.partner_ids.ids
            self.ine_activate = res

class entidad(models.Model):
    _name = "account.invoice.ine.entidad"
    
    invoice_id = fields.Many2one("account.invoice", "Factura")
    state_id = fields.Many2one('res.country.state', string='Estado', required=True)
    ambito = fields.Selection([
            ('Local', 'Local'),
            ('Federal', 'Federal')],
        string=u"Ámbito", help="""Este atributo no se debe registrar para los procesos de tipo Ordinario""")
    contabilidad = fields.One2many("account.invoice.ine.contabilidad", "line_id", string="Contabilidad")

    # Quitar futuras versiones
    clave_entidad = fields.Selection([
            (x,x) for x in claves_entidades], 
        string="Clave Entidad", required=False)


class contabilidad(models.Model):
    _name = "account.invoice.ine.contabilidad"
    
    id_contabilidad = fields.Integer("Id Contabilidad", required=True)
    line_id = fields.Many2one("account.invoice.ine.entidad", string="Entidad")