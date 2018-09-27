# -*- coding: utf-8 -*-

import json
import odoo
from odoo import models, fields, api, _

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

    """
    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountInvoice, self).register_payment(payment_line, writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        if self.env.context.get('invoice_id') and self.env.context.get('payment_id'):
            payment_id = self.env.context["payment_id"]
            if payment_id.filtered(lambda r: r.cfdi_is_required()):
                payment_id.action_validate_cfdi()
        return res
    """

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