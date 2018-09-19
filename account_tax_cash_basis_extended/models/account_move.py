# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import UserError, Warning
from operator import itemgetter


#----------------------------------------------------------
# Entries
#----------------------------------------------------------
class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('journal_id')
    def _fiscal(self):
        for move in self:
            move.show_fiscal = move.journal_id.type in ('bank','cash')


    fiscal_ids = fields.One2many('account.move.fiscal', 'move_id', string='Fiscal Entries')
    show_fiscal = fields.Boolean(compute='_fiscal', store=True)

    @api.multi
    def open_cash_basis_view(self):
        [action] = self.env.ref('account.action_move_journal_line').read()
        cash_basis_movs = self.env['account.move']
        obj = self.env['account.partial.reconcile']
        if self.tax_cash_basis_rec_id:
            cash_basis_movs |= self.tax_cash_basis_rec_id.credit_move_id.move_id
            cash_basis_movs |= self.tax_cash_basis_rec_id.debit_move_id.move_id
        for line in self.line_ids.filtered(lambda l: l.account_id.reconcile):
            rec_ids = obj.search(['|',('credit_move_id', 'in', line._ids),('debit_move_id', 'in', line._ids)])
            cash_basis_movs |= rec_ids.filtered(lambda l: l.credit_move_id).mapped('credit_move_id.move_id')
            cash_basis_movs |= rec_ids.filtered(lambda l: l.debit_move_id).mapped('debit_move_id.move_id')
            cash_basis_movs |= line.mapped('full_reconcile_id.reconciled_line_ids.move_id')
        line_ids = self.line_ids.filtered(lambda l: l.reconciled).ids
        tax_cash_basis_rec_ids = obj.search(['|',('credit_move_id', 'in', line_ids),('debit_move_id', 'in', line_ids)])
        lin_obj = self.env['account.move']
        cash_basis_movs |= lin_obj.search([('tax_cash_basis_rec_id', 'in', tax_cash_basis_rec_ids.ids)])
        action['domain'] = [('id', 'in', cash_basis_movs.ids)]
        action['context'] = "{'search_default_misc_filter':0}"
        return action

    @api.multi
    def get_cash_basis_movs(self):
        cash_basis_movs = []
        credit_move_id, debit_move_id = False, False
        # Cash Basis Move Entry
        if self.tax_cash_basis_rec_id:
            cash_basis_movs.extend([self.tax_cash_basis_rec_id.credit_move_id.move_id, self.tax_cash_basis_rec_id.debit_move_id.move_id])
        # Reconciled Move Entries (Bank or Cash and Invoice)
        elif not cash_basis_movs:
            for line in [l for l in self.line_ids if l.account_id.reconcile]:
                rec_ids = self.env['account.partial.reconcile'].search(['|',('credit_move_id', 'in', line._ids),('debit_move_id', 'in', line._ids)])
                cash_basis_movs = [x for x in self.env['account.move'].search([('tax_cash_basis_rec_id', 'in', rec_ids._ids)])]
        return cash_basis_movs, False

    @api.model
    def get_invoice(self, credit_move_id, debit_move_id): 
        invoice = False
        if credit_move_id and debit_move_id:
            invoice_move_ids = [m.id for m in [credit_move_id, debit_move_id] if m.journal_id.type not in ('bank','cash')]
            invoice = self.env['account.invoice'].search([('move_id', 'in', invoice_move_ids)])
        return invoice

    @api.multi
    def button_create_fiscal(self): 
        # Bank Move Entry
        for move in self:
            for line in move.line_ids:
                line.create_fiscal_line()

    @api.multi
    def button_delete_fiscal(self):
        # Bank Move Entry
        for move in self:
            if move.fiscal_ids:
                move.fiscal_ids.sudo().unlink()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #####################################################################################################################
    ## CREATE account_move_fiscal Lines and create tax transfer account_move_line
    #####################################################################################################################
    @api.model
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        res.move_id.button_create_fiscal()
        return res

    @api.multi
    def create_fiscal_line(self):
        # >>>>>>>>>>    Return if journal is not bank or cash
        if not self.journal_id.type in ('bank','cash'): 
            return
        operation_type = self.get_operation_type()
        if not operation_type: 
            return
        # >>>>>>>>>>    Return if line debit and credit in zero
        elif not self.debit - self.credit:
            return
        # >>>>>>>>>>    Get tax and base amounts
        elif self in [x.line_id for x in self.move_id.fiscal_ids]:
            return
        vals = self.get_base(operation_type)
        if not vals:
            return
        vals.update({
            'line_id': self.id,
            'operation_type': operation_type,
        })
        self.env['account.move.fiscal'].sudo().create(vals)
        return

    #####################################################################################################################
    #   Return type of operation
    #####################################################################################################################
    @api.multi
    def get_operation_type(self):
        query = """SELECT default_debit_account_id FROM account_journal WHERE type in ('bank','cash') UNION 
                   SELECT default_credit_account_id FROM account_journal WHERE type in ('bank','cash') """
        self._cr.execute(query)
        bank_accounts = map(itemgetter(0), self._cr.fetchall())
        operation_type = False
        bank_acc_ids = [self.journal_id.default_debit_account_id, self.journal_id.default_credit_account_id]
        if self.account_id in bank_acc_ids:                                                                             # >>>>>>>>>> line account is the same that bank journal account
            pass
        elif self.account_id.id in bank_accounts:                                                                       # >>>>>>>>>> inter-bank outcome/income line
            operation_type = (self.debit - self.credit) > 0 and 'inter_bank_out' or 'inter_bank_in'                     
        elif (self.debit - self.credit) == 0: 
            operation_type = 'null'
        else:
            bnk_line_ids = [x for x in self.move_id.line_ids if x.account_id in bank_acc_ids]
            if bnk_line_ids:
                bnk_line = bnk_line_ids[0]
                operation_type = (bnk_line.debit - bnk_line.credit) < 0 and 'outcome' or 'income'                        # >>>>>>>>>> trigger outcome/income line
        return operation_type

    #####################################################################################################################
    ## Get taxes: base, vat, ieps, retensions (vat and isr) from account_move_fiscal Lines
    #####################################################################################################################
    @api.multi
    def get_base(self, operation_type):
        def compute(amount, currency, date):
            ctx = {'date':date}
            if currency:
                return currency.with_context(ctx).compute(amount, self.company_id.currency_id)
            else:
                return amount           
        sign = (self.credit-self.debit) > 0 and 1 or -1
        payment_total = abs(self.credit-self.debit) * sign
        journal_currency = self.journal_id.currency_id or self.company_id.currency_id
        res = {'payment_total':payment_total, 'currency_id':journal_currency.id}
        if (operation_type in ('outcome', 'income')):
            if self.full_reconcile_id:
                inv_lines = self.search([('full_reconcile_id','=',self.full_reconcile_id.id),('id','!=',self.id)])
                move_ids = [x.move_id.id for x in inv_lines if x.move_id]
                invoice_ids = self.env['account.invoice'].search([('move_id','in',move_ids)])
                if invoice_ids:
                    invoice = invoice_ids[0]
                    invoice_currency = invoice.currency_id
                    res.update({'invoice_id':invoice.id, 'invoice_total':invoice.amount_total_company_signed})
                    #if sum([x.amount_currency for x in invoice.payment_move_line_ids]):
                        #payment_total = compute(abs(sum([x.amount_currency for x in invoice.payment_move_line_ids])), invoice_currency, self.date) * sign
                    #else:
                        #payment_total = abs(sum([x.credit-x.debit for x in invoice.payment_move_line_ids])) * sign
                    
                    invoice_total = compute(invoice.amount_total, invoice_currency, self.date)
                    factor = invoice_total and abs(payment_total/invoice_total)
                    for tax_line in invoice.tax_line_ids:
                        for tag in tax_line.tax_id.tag_ids:
                            if tag:
                                tax_amount = compute(tax_line.amount, invoice_currency, self.date) * factor * sign
                                base_amount = compute(tax_line.base, invoice_currency, self.date) * factor
                                self._cr.execute('select name from account_account_tag where id=%s'%tag.id)
                                name = self._cr.fetchone()[0]
                                if 'TAX ' in name:
                                    section = name.replace("TAX ","")
                                    res.update({
                                        'tax_%s'%section:tax_amount,
                                        'base_%s'%section:base_amount,
                                    })
            else: #TODO Enhance the tax without invoice calculation
                config_ids = self.env['ir.config_parameter'].search([('key','=','default_diot_tax')])
                if config_ids:
                    # {'default':'tax_3,
                    # 'tax_0':1,    - IVA 0%
                    # 'tax_1':1,    - IVA Excento
                    # 'tax_2':1,    - IVA Excento en Importaciones
                    # 'tax_3':12,   - IVA 16% en compras o ventas
                    # 'tax_4':13,   - IVA 16% en compras o ventas usado en pedimentos
                    # 'tax_5':1,    - IVA no no acreditable
                    # 'tax_6':4,    - Retencion de IVA 4% en fletes
                    # 'tax_7':8,    - Retencion de IVA 10% en arrendamientos
                    # 'tax_8':9,    - Retencion de IVA 10.67% en servicios profesionales
                    # 'tax_9':7, }  - Retencion de ISR 10% en servicios profesionales y arrendamientos
                    #
                    # Supplier Type 04:Proveedor Nacional, 05:Proveedor Extranjero, 15:Proveedor Global
                    # Operation Type: 03:Prestacion de Servicios Profecionales, 06:Arrendamiento de Inmuebles, 85:Otros
                    # 
                    value = config_ids[0].value and eval(config_ids[0].value)
                    tax_default = value and value.get('default') and value.get(value['default'])
                    tax_1 = value and value.get('tax_1')
                    tax_3 = value and value.get('tax_3')
                    tax_8 = value and value.get('tax_8')
                    tax_9 = value and value.get('tax_9')
                    if self.partner_id:
                        supplier_type = self.partner_id.supplier_type
                        operation_type = self.partner_id.operation_type
                        if supplier_type == '04': # Proveedor Nacional
                            if operation_type == '03' and tax_3 and tax_8 and tax_9: # Prestacion de Servicios Profecionales
                                amount_03 = self.env['account.tax'].browse(tax_3).amount/100
                                amount_08 = self.env['account.tax'].browse(tax_8).amount/100
                                amount_09 = self.env['account.tax'].browse(tax_9).amount/100
                                subtotal = payment_total/(1 + amount_03 + amount_08 + amount_09)
                                res.update({
                                    'tax_%s'%3:subtotal * amount_03 * sign,
                                    'base_%s'%3:subtotal * sign,
                                    'tax_%s'%8:subtotal * amount_08 * sign,
                                    'base_%s'%8:subtotal * sign,
                                    'tax_%s'%9:subtotal * amount_09 * sign,
                                    'base_%s'%9:subtotal * sign,
                                })
                            elif operation_type == '06' and tax_3 and tax_7 and tax_9: # Arrendamiento de Inmuebles
                                amount_03 = self.env['account.tax'].browse(tax_3).amount/100
                                amount_07 = self.env['account.tax'].browse(tax_7).amount/100
                                amount_09 = self.env['account.tax'].browse(tax_9).amount/100
                                subtotal = payment_total/(1 + amount_03 + amount_07 + amount_09)
                                res.update({
                                    'tax_%s'%3:subtotal * amount_03 * sign,
                                    'base_%s'%3:subtotal * sign,
                                    'tax_%s'%7:subtotal * amount_07 * sign,
                                    'base_%s'%7:subtotal * sign,
                                    'tax_%s'%9:subtotal * amount_09 * sign,
                                    'base_%s'%9:subtotal * sign,
                                })
                            elif operation_type == '85' and tax_3: # Otros
                                amount_03 = self.env['account.tax'].browse(tax_3).amount/100
                                subtotal = payment_total/(1 + amount_03)
                                res.update({
                                    'tax_%s'%3:subtotal * amount_03 * sign,
                                    'base_%s'%3:subtotal * sign,
                                })
                        elif supplier_type == '05' and tax_1: # Proveedor Extranjero
                            amount_01 = self.env['account.tax'].browse(tax_1).amount/100
                            subtotal = payment_total/(1 + amount_01)
                            res.update({
                                'tax_%s'%1:subtotal * amount_01 * sign,
                                'base_%s'%1:subtotal * sign,
                            })
                        else:
                            amount_default = self.env['account.tax'].browse(tax_default).amount/100
                            subtotal = payment_total/(1 + amount_default)
                            res.update({
                                'tax_%s'%1:subtotal * amount_default * sign,
                                'base_%s'%1:subtotal * sign,
                            })

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
