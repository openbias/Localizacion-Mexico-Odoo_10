# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

from operator import itemgetter

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class account_account(models.Model):

    _name = "account.account"
    _inherit="account.account"
    _description = "Account"

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'code'
    _order = 'parent_left'

    @api.multi
    def get_level(self):
        for account in self:
            level = 0
            parent = account.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
        return level

    @api.one
    @api.depends('parent_id', 'parent_left', 'parent_right')
    def _get_level(self):
        self.level = self.get_level()

    @api.multi
    def _get_children_and_consol(self):
        # this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search([('parent_id', 'child_of', self.ids)])
        return ids2

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """
        ctx = dict(self._context)
        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        if 'partner_id' in ctx:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get(domain=[('partner_id', '=', ctx['partner_id'] )])
        elif 'not_partner_id' in ctx:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get(domain=[('partner_id', '=', False )])
        # elif 'partner_ids' in ctx:
        #     tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=[('partner_id', 'in', ctx['partner_ids'] )])
        else:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get()
            
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.one
    def _compute_amount(self):
        dp = self.env['decimal.precision'].precision_get('Account')
        self._cr.execute("""SELECT COALESCE(MIN(date), NOW()::DATE) AS "min", COALESCE(MAX(date), NOW()::DATE) AS "max" from account_move_line""")
        dates = self._cr.dictfetchone()
        ctx = dict(self._context)

        date_from = ctx.get('date_from') and ctx['date_from'] or dates['min']
        date_to  = ctx.get('date_to')   and ctx['date_to']   or dates['max']
        data = {
            'form': {
                'display_account': u'movement', 
                'date_from': date_from, 
                'date_to': date_to,
                'journal_ids': ctx.get('journal_ids'),
                'id': 143,
                'target_move': ctx.get('state'),
                'used_context': {
                    u'lang': ctx.get('lang'),
                    u'date_from': date_from,
                    u'date_to': date_to,
                    u'journal_ids': ctx.get('journal_ids'),
                    u'state': ctx.get('state'),
                    u'strict_range': True,
                    
                }
            }
        }
        account_obj = self.env['account.account']
        trialbalance = self.env['report.account.report_trialbalance']
        self.model = self.env.context.get('active_model')        
        # docs = self.env['self.model'].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')

        accounts = self._get_children_and_consol()
        date_from = datetime.strptime(data['form'].get('date_from'), '%Y-%m-%d').date()
        date_to = datetime.strptime(data['form'].get('date_to'), '%Y-%m-%d').date()

        initial = 0.0
        debit = 0.0
        credit = 0.0
        balance = 0.0
        used_context = data['form'].get('used_context')
        if 'partner_id' in ctx:
            used_context['partner_id'] = ctx['partner_id']
        if 'not_partner_id' in ctx:
            used_context['not_partner_id'] = True
        # elif 'partner_ids' in ctx:
        #     used_context['partner_ids'] = ctx['partner_ids']
        for acc_brw in accounts:
            account_res = self.with_context(used_context)._get_accounts(acc_brw, display_account)
            account = {}
            for account in account_res:
                credit += account['credit']
                debit += account['debit']
            date_to = date_from # + relativedelta(days=-1)
            line_used_context = used_context.copy()
            line_used_context['date_to'] = str(date_to)
            line_used_context['date_from'] = '%s-01-01'%(date_to.year)
            
            # print "acc_brw.user_type_id.es_resultado", acc_brw.user_type_id.es_resultado
            # if acc_brw.user_type_id.es_resultado:
            #     line_used_context['date_from'] = '%s-01-01'%(date_to.year)
            
            if acc_brw.user_type_id.include_initial_balance == True:
                line_used_context['strict_range'] = False

            vals = self.with_context(line_used_context)._get_accounts(acc_brw, display_account)
            for val in vals:
                bal = round(val['balance'], dp)
                bal1 = (bal + account.get('debit', 0.0) - account.get('credit', 0.0))
                initial += bal
        balance =  initial + debit - credit

        self.initial = initial
        self.debit = debit
        self.credit = credit
        self.balance = balance

    level = fields.Integer(string='Account Level', compute="_get_level", index=True, store=True)
    parent_id = fields.Many2one('account.account', 'Parent', index=True, ondelete='cascade', domain=[('internal_type' ,'=' ,'view')])
    child_id = fields.One2many('account.account', 'parent_id', 'Child Accounts')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)

    children_ids = fields.One2many('account.account', 'parent_id', 'Children')
    child_consol_ids = fields.Many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id', 'Consolidated Children')
    
    initial = fields.Float(string = "Initial", compute='_compute_amount', track_visibility='always')
    balance = fields.Float(string = "Balance", compute='_compute_amount', track_visibility='always')
    credit = fields.Float(string='Credit', compute='_compute_amount', track_visibility='always')
    debit = fields.Float(string='Debit', compute='_compute_amount', track_visibility='always')

    type = fields.Selection([], 'Account Type', 
        help="The 'Internal Type' is used for features available on " \
            "different types of accounts: view can not have journal items, consolidation are accounts that " \
            "can have children accounts for multi-company consolidations, payable/receivable are for " \
            "partners accounts (for debit/credit computations), closed for depreciated accounts.") # TODO remove this field...

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True
    
    # @api.constrains('user_type_id')
    # @api.one
    # def _check_type(self):
    #     if self.children_ids and self.user_type_id.type != 'view':
    #         raise ValidationError(_('Configuration Error!\nYou cannot define children to an account with internal type different of "View".'))

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if not context.get('view_all', False):
            args += [('internal_type', '!=', 'view')]
        return super(account_account, self).search(args, offset=offset, limit=limit, order=order, count=count)


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    # @api.one
    # @api.depends('type')
    # def _get_esresultado(self):
    #     for ttype in self:
    #         income_id = self.env.ref('account.data_account_type_other_income')
    #         revenue_id = self.env.ref('account.data_account_type_revenue')
    #         depreciation_id = self.env.ref('account.data_account_type_depreciation')
    #         expenses_id = self.env.ref('account.data_account_type_expenses')
    #         direct_costs_id = self.env.ref('account.data_account_type_direct_costs')
    #         self.es_resultado = (ttype.id in [income_id.id, revenue_id.id, depreciation_id.id, expenses_id.id, direct_costs_id.id])
    # include_initial_balance = False = Resultado
    
    # es_resultado = fields.Boolean(compute=_get_esresultado, string='Es resultado ? ', store=True)
    es_resultado = fields.Boolean(string="Es resultado ? ")
    type = fields.Selection(selection_add=[
        ('view','View')
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.")

