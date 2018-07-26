# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ReasonCancelInvoice(models.TransientModel):
    _name = "reason.cancel.invoice"

    name = fields.Char(string='Name')
    reason_cancel = fields.Char(string='Motivo Cancelacion')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')

    @api.model
    def default_get(self, fields):
        res = super(ReasonCancelInvoice, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        inv = self.env['account.invoice'].browse(active_id)
        res = {
            'invoice_id': inv.id
        }
        return res



    @api.multi
    def action_reason_cancel_invoice(self):
        print 'r'

        return True