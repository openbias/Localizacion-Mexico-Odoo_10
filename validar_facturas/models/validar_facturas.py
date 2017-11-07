# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    creada_de_xml = fields.Boolean(string="Creada a partir de CFDI", default=False, copy=False)

    @api.multi
    def action_subir_xml(self):
        context = dict(self.env.context or {})
        context['active_ids'] = [self.id]
        context['active_id'] = self.id
        context["active_model"] = "account.invoice"
        # context["inv_create"] = True

        data_obj = self.env['ir.model.data']
        view = data_obj.xmlid_to_res_id('validar_facturas.validar_facturas_form')
        wiz_id = self.env['validar.facturas'].create({})
        return {
             'name': _('Subir XML y PDF'),
             'type': 'ir.actions.act_window',
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'validar.facturas',
             'views': [(view, 'form')],
             'view_id': view,
             'target': 'new',
             'res_id': wiz_id.id,
             'context': context,
         }