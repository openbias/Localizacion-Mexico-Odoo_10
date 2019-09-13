# -*- coding: utf-8 -*-

from odoo import models, fields, api

class leyendasFiscales(models.Model):
    _name = 'cfd_mx.leyendasfiscales'

    name = fields.Char("Leyenda", required=True)
    norma = fields.Char("Norma")
    disposicion_fiscal = fields.Char("Disposicion Fiscal")


class addendas(models.Model):
    _inherit = 'cfd_mx.conf_addenda'

    model_selection = fields.Selection(selection_add=[('complemento_leyendas_fiscales', 'Complemento Leyendas Fiscales')])

    def complemento_leyendas_fiscales_create_addenda(self, invoice):
        context = self._context or {}
        leyendas_attribs = {}
        leyendas_attribs["Version"]= "1.1"
        leyenda_attribs = []
        print "------------------------"
        print "invoice.leyendasfiscales_ids", invoice.leyendasfiscales_ids
        for leyenda in invoice.leyendasfiscales_ids:
            leyenda_attribs_tmp = {
                'textoLeyenda': leyenda.name
            }
            if leyenda.norma:
                leyenda_attribs_tmp['norma'] = leyenda.norma
            if leyenda.disposicion_fiscal:
                leyenda_attribs_tmp['disposicionFiscal'] = leyenda.disposicion_fiscal
            leyenda_attribs.append(leyenda_attribs_tmp)
        dict_addenda = {
            'type': 'Complemento',
            'name': self.model_selection,
            'addenda':{
                'leyendas_attribs': leyendas_attribs,
                'leyendas': leyenda_attribs
            }
        }
        print "dict_addenda", dict_addenda
        return dict_addenda


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    leyendas_fiscales_activate = fields.Boolean("Activar Leyendas")
    leyendasfiscales_ids = fields.Many2many('cfd_mx.leyendasfiscales', string="Leyendas Fiscales")

    @api.model
    def create(self, vals):
        onchanges = {
            'onchange_activateleyendas': ['partner_id'],
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
    def onchange_activateleyendas(self):
        if not self.partner_id:
            self.update({
                'leyendas_fiscales_activate': False,
            })
            return

        conf_addenda = self.env['cfd_mx.conf_addenda']
        conf_addenda_id = conf_addenda.search([('model_selection','=', 'complemento_leyendas_fiscales'), ('company_id', '=', self.company_id.id)])
        if conf_addenda_id:
            res = self.partner_id.id in conf_addenda_id.partner_ids.ids
            self.leyendas_fiscales_activate = res