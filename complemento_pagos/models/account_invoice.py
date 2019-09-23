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

    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountInvoice, self).register_payment(payment_line, writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)

        if self._context.get('factoring', False):
            return res
        if not self:
            return res
        for inv in self:
            if inv.type.startswith("in"):
                return res
        if payment_line.payment_id and payment_line.payment_id:
            ctx_inv = {}
            for record in payment_line.payment_id.filtered(lambda r: r.cfdi_validate_required()):
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
            if payment_line.payment_id.filtered(lambda r: r.cfdi_validate_required()):
                payment_line.payment_id.with_context(ctx_inv=ctx_inv).action_validate_cfdi()
        return res


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