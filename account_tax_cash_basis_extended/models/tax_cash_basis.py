# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from odoo.exceptions import UserError
from openerp.tools import float_compare, float_is_zero


#----------------------------------------------------------
# Partial Reconcile
#----------------------------------------------------------
class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    name = fields.Char(required=True, translate=True)

#----------------------------------------------------------
# Partial Reconcile
#----------------------------------------------------------
class AccountPartialReconcileCashBasis(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.multi
    def create(self, vals):
        res = super(AccountPartialReconcileCashBasis, self).create(vals)
        res.credit_move_id.create_fiscal_line()
        res.debit_move_id.create_fiscal_line()
        return res

    @api.multi
    def unlink(self):
        lines = []
        for line in self:
            if line.credit_move_id.journal_id.type == 'bank':
                lines.append(line.credit_move_id)
            elif line.debit_move_id.journal_id.type == 'bank':
                lines.append(line.debit_move_id)
        ids = []
        for aml in lines:
            fiscal = self.env['account.move.fiscal'].search([('line_id','=',aml.id)])
            if fiscal:
                fiscal.unlink()
        super(AccountPartialReconcileCashBasis, self).unlink()

    def _get_tax_cash_basis_lines_old(self, value_before_reconciliation):
        # Search in account_move if we have any taxes account move lines
        tax_group = {}
        total_by_cash_basis_account = {}
        line_to_create = []
        move_date = self.debit_move_id.date
        for move in (self.debit_move_id.move_id, self.credit_move_id.move_id):# account.move(44109,) - account.move(42858,)
            if move_date < move.date:
                move_date = move.date
            for line in move.line_ids:
                #TOCHECK: normal and cash basis taxes shoudn't be mixed together (on the same invoice line for example) as it will
                #create reporting issues. Not sure of the behavior to implement in that case, though.
                # amount to write is the current cash_basis amount minus the one before the reconciliation
                currency_id = line.currency_id or line.company_id.currency_id
                matched_percentage = value_before_reconciliation[move.id]
                amount = currency_id.round((line.credit_cash_basis - line.debit_cash_basis) - (line.credit - line.debit) * matched_percentage)
                if not float_is_zero(amount, precision_rounding=currency_id.rounding) and not line.tax_exigible:
                    if line.tax_line_id and line.tax_line_id.use_cash_basis:
                        # group by line account
                        acc = line.account_id.id
                        if tax_group.get(acc, False):
                            tax_group[acc] += amount
                        else:
                            tax_group[acc] = amount
                        # Group by cash basis account and tax
                        acc = line.tax_line_id.cash_basis_account.id
                        if not acc:
                            raise UserError(_('Please configure a Tax Received Account for tax %s') % line.tax_line_id.name)
                        key = (acc, line.tax_line_id.id)
                        if key in total_by_cash_basis_account:
                            total_by_cash_basis_account[key] += amount
                        else:
                            total_by_cash_basis_account[key] = amount
                    #####################################################################################
                    # This section is commented to eliminate the non tax lines in cash basis entry 
                    #####################################################################################
                    #if any([tax.use_cash_basis for tax in line.tax_ids]):
                    #    for tax in line.tax_ids:
                    #        line_to_create.append((0, 0, {
                    #            'name': '/',
                    #            'debit': currency_id.round(line.debit_cash_basis - line.debit * matched_percentage),
                    #            'credit': currency_id.round(line.credit_cash_basis - line.credit * matched_percentage),
                    #            'account_id': line.account_id.id,
                    #            'tax_ids': [(6, 0, [tax.id])],
                    #            }))
                    #        line_to_create.append((0, 0, {
                    #            'name': '/',
                    #            'credit': currency_id.round(line.debit_cash_basis - line.debit * matched_percentage),
                    #            'debit': currency_id.round(line.credit_cash_basis - line.credit * matched_percentage),
                    #            'account_id': line.account_id.id,
                    #            }))

        for k, v in tax_group.items():
            line_to_create.append((0, 0, {
                'name': '/',
                'debit': v if v > 0 else 0.0,
                'credit': abs(v) if v < 0 else 0.0,
                'account_id': k,
                'tax_exigible': True,
            }))

        # Create counterpart vals
        for key, v in total_by_cash_basis_account.items():
            k, tax_id = key
            # Only entries with cash flow must be created
            if not self.company_id.currency_id.is_zero(v):
                line_to_create.append((0, 0, {
                    'name': '/',
                    'debit': abs(v) if v < 0 else 0.0,
                    'credit': v if v > 0 else 0.0,
                    'account_id': k,
                    'tax_line_id': tax_id,
                    'tax_exigible': True,
                }))
        return line_to_create, move_date

#----------------------------------------------------------
# Account Move Fiscal
#----------------------------------------------------------
class AccountMoveFiscal(models.Model):
    _name = "account.move.fiscal"
    _description = "Fiscal Entries"
    _rec_name = 'line_id'
    _order = 'date'

    line_id = fields.Many2one('account.move.line', string='Bank Journal Line', readonly=True)
    move_id = fields.Many2one('account.move', related="line_id.move_id", ondelete="cascade", readonly=True, store=True)
    journal_id = fields.Many2one('account.journal', related="line_id.move_id.journal_id", store=True)
    ref = fields.Char(related="line_id.move_id.ref", store=True)
    invoice_name = fields.Char(related="line_id.move_id.name", store=True)
    vat = fields.Char(related="line_id.partner_id.vat", store=True)
    date = fields.Date('date', related="line_id.date", store=True)
    partner_id = fields.Many2one('res.partner', related="line_id.partner_id", store=True)
    account_id = fields.Many2one('account.account', related="line_id.account_id", store=True)
    company_id = fields.Many2one('res.company', related="line_id.company_id", store=True, string='Company')
    company_currency_id = fields.Many2one('res.currency', related='line_id.company_id.currency_id', string='Company Currency', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_before_retension = fields.Monetary(default=0.0, currency_field='company_currency_id', readonly=True, string='Amount Before Retension')
    invoice_total = fields.Monetary(default=0.0, currency_field='company_currency_id', string='Invoice Total', readonly=True)
    payment_total = fields.Monetary(default=0.0, currency_field='company_currency_id', string='Total Payment', readonly=True)
    xfer_ids = fields.Many2many('account.move.line', readonly=True)
    invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    operation_type = fields.Selection([
        ('inter_bank_out', 'Interbank Outcome'),
        ('inter_bank_in', 'Interbank Income'),
        ('null', 'Null'),
        ('outcome', 'Outcome'),
        ('income','Income')], string='operation_type', readonly=True)
    base_0 = fields.Monetary(string='Base 0', default=0.0, currency_field='company_currency_id')
    base_1 = fields.Monetary(string='Base 1', default=0.0, currency_field='company_currency_id')
    base_2 = fields.Monetary(string='Base 2', default=0.0, currency_field='company_currency_id')
    base_3 = fields.Monetary(string='Base 3', default=0.0, currency_field='company_currency_id')
    base_4 = fields.Monetary(string='Base 4', default=0.0, currency_field='company_currency_id')
    base_5 = fields.Monetary(string='Base 5', default=0.0, currency_field='company_currency_id')
    base_6 = fields.Monetary(string='Base 6', default=0.0, currency_field='company_currency_id')
    base_7 = fields.Monetary(string='Base 7', default=0.0, currency_field='company_currency_id')
    base_8 = fields.Monetary(string='Base 8', default=0.0, currency_field='company_currency_id')
    base_9 = fields.Monetary(string='Base 9', default=0.0, currency_field='company_currency_id')
    base_a = fields.Monetary(string='Base a', default=0.0, currency_field='company_currency_id')
    base_b = fields.Monetary(string='Base b', default=0.0, currency_field='company_currency_id')
    base_c = fields.Monetary(string='Base c', default=0.0, currency_field='company_currency_id')
    base_d = fields.Monetary(string='Base d', default=0.0, currency_field='company_currency_id')
    base_e = fields.Monetary(string='Base e', default=0.0, currency_field='company_currency_id')
    base_f = fields.Monetary(string='Base f', default=0.0, currency_field='company_currency_id')
    tax_0 = fields.Monetary(string='Tax 0', default=0.0, currency_field='company_currency_id')
    tax_1 = fields.Monetary(string='Tax 1', default=0.0, currency_field='company_currency_id')
    tax_2 = fields.Monetary(string='Tax 2', default=0.0, currency_field='company_currency_id')
    tax_3 = fields.Monetary(string='Tax 3', default=0.0, currency_field='company_currency_id')
    tax_4 = fields.Monetary(string='Tax 4', default=0.0, currency_field='company_currency_id')
    tax_5 = fields.Monetary(string='Tax 5', default=0.0, currency_field='company_currency_id')
    tax_6 = fields.Monetary(string='Tax 6', default=0.0, currency_field='company_currency_id')
    tax_7 = fields.Monetary(string='Tax 7', default=0.0, currency_field='company_currency_id')
    tax_8 = fields.Monetary(string='Tax 8', default=0.0, currency_field='company_currency_id')
    tax_9 = fields.Monetary(string='Tax 9', default=0.0, currency_field='company_currency_id')
    tax_a = fields.Monetary(string='Tax a', default=0.0, currency_field='company_currency_id')
    tax_b = fields.Monetary(string='Tax b', default=0.0, currency_field='company_currency_id')
    tax_c = fields.Monetary(string='Tax c', default=0.0, currency_field='company_currency_id')
    tax_d = fields.Monetary(string='Tax d', default=0.0, currency_field='company_currency_id')
    tax_e = fields.Monetary(string='Tax e', default=0.0, currency_field='company_currency_id')
    tax_f = fields.Monetary(string='Tax f', default=0.0, currency_field='company_currency_id')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

