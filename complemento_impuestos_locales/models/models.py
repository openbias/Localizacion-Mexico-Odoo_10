# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def _compute_imp_loc_activate(self):
        active = False
        imploc_tras_id = self.env.ref('cfd_mx.tax_group_tras_loc')
        imploc_ret_id = self.env.ref('cfd_mx.tax_group_ret_loc')
        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id.id in [imploc_tras_id.id, imploc_ret_id.id]:
                active = True
        self.imp_loc_activate = active

    imp_loc_activate = fields.Boolean("Activar", compute="_compute_imp_loc_activate")



    @api.multi
    def get_comprobante_addenda(self):
        context = dict(self._context) or {}
        if self.imp_loc_activate:
            TotaldeRetenciones = 0.0
            TotaldeTraslados = 0.0
            imploc_ret_attribs = []
            imploc_tras_attribs = []
            
            imploc_ret_id = self.env.ref('cfd_mx.tax_group_ret_loc')
            imploc_tras_id = self.env.ref('cfd_mx.tax_group_tras_loc')
            for tax in self.tax_line_ids:
                if tax.tax_id.tax_group_id.id == imploc_ret_id.id:
                    t = {
                        'ImpLocRetenido': tax.tax_id.description,
                        'TasadeRetencion': '%.2f'%tax.tax_id.amount,
                        'Importe': '%.2f'%tax.amount
                    }
                    imploc_ret_attribs.append(t)
                    TotaldeRetenciones += tax.amount
                if tax.tax_id.tax_group_id.id == imploc_tras_id.id:
                    t = {
                        'ImpLocTrasladado': tax.tax_id.description,
                        'TasadeTraslado': '%.2f'%tax.tax_id.amount,
                        'Importe': '%.2f'%tax.amount
                    }
                    imploc_tras_attribs.append(t)
                    TotaldeTraslados += tax.amount


            imploc_attribs = {
                'TotaldeRetenciones': '%.2f'%TotaldeRetenciones,
                'TotaldeTraslados': '%.2f'%TotaldeTraslados
            }
            dict_addenda = {
                'type': 'Complemento',
                'name': 'complemento_impuestos_locales',
                'addenda':{
                    'imploc_attribs': imploc_attribs,
                    'imploc_ret_attribs': imploc_ret_attribs,
                    'imploc_tras_attribs': imploc_tras_attribs
                }
            }
            print 'dict_addenda', dict_addenda
            return dict_addenda
        else:
            return super(AccountInvoice, self).get_comprobante_addenda()



# class complemento_impuestos_locales(models.Model):
#     _name = 'complemento_impuestos_locales.complemento_impuestos_locales'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100