# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountAccount(models.Model):
    _inherit = 'account.account'

    codigo_agrupador_id = fields.Many2one('contabilidad_electronica.codigo.agrupador', 
                string="Codigo agrupador SAT", oldname="codigo_agrupador")
    naturaleza_id = fields.Many2one('contabilidad_electronica.naturaleza', 
                string="Naturaleza", oldname="naturaleza")


    def _compute_initial_balance_partners(self, account_ids):
        params = (tuple( account_ids ),)
        query = "SELECT DISTINCT(l.partner_id) AS partner_id FROM account_move_line l WHERE l.account_id in %s"
        self._cr.execute(query, params)
        partner_ids = [x[0] for x in self._cr.fetchall()]
        return partner_ids


    def _compute_initial_balance_datas(self, accounts, display_account):
        ctx = dict(self._context)
        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        if 'partner_id' in ctx:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get(domain=[('partner_id', '=', ctx['partner_id'] )])
        elif 'not_partner_id' in ctx:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(ctx)._query_get(domain=[('partner_id', '=', False )])
        elif 'partner_ids' in ctx:
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=[('partner_id', 'in', ctx['partner_ids'] )])
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
            res['code'] = account.code_alias
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


    def _compute_initial_balance(self, ctx):
        unaffected_earnings_id = self.env.ref('account.data_unaffected_earnings')
        ContextCoa = self.env['account.context.coa']
        CoaReport = self.env['account.coa.report']
        uid = self.env.user.id
        company_id = self.env.user.company_id

        dp = self.env['decimal.precision'].precision_get('Account')
        self._cr.execute("""SELECT COALESCE(MIN(date), NOW()::DATE) AS "min", COALESCE(MAX(date), NOW()::DATE) AS "max" from account_move_line""")
        dates = self._cr.dictfetchone()
        date_from_orig = ctx.get('date_from') and ctx['date_from'] or dates['min']
        date_to_orig  = ctx.get('date_to')   and ctx['date_to']   or dates['max']
        data = {
            'form': {
                'display_account': u'movement',
                'date_from': date_from_orig,
                'date_to': date_to_orig,
                'journal_ids': ctx.get('journal_ids'),
                'id': 143,
                'target_move': ctx.get('state'),
                'used_context': {
                    u'lang': ctx.get('lang'),
                    u'date_from': date_from_orig,
                    u'date_to': date_to_orig,
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
        date_from = datetime.strptime(data['form'].get('date_from'), '%Y-%m-%d').date()
        date_to = datetime.strptime(data['form'].get('date_to'), '%Y-%m-%d').date()

        initial, debit, credit, balance = 0.0, 0.0, 0.0, 0.0
        used_context = data['form'].get('used_context')
        if 'partner_id' in ctx:
            used_context['partner_id'] = ctx['partner_id']
        elif 'not_partner_id' in ctx:
            used_context['not_partner_id'] = True
        elif 'partner_ids' in ctx:
            used_context['partner_ids'] = ctx['partner_ids']
        for acc_brw in self:
            account_res = self.with_context(used_context)._compute_initial_balance_datas(acc_brw, display_account)
            for account in account_res:
                credit += account['credit']
                debit += account['debit']
            if unaffected_earnings_id == acc_brw.user_type_id:
                context_coa_id = ContextCoa.search([], limit=1)
                if context_coa_id:
                    context_coa_id.write({
                        'date_from': date_from_orig,
                        'date_to': date_to_orig,
                        'date_filter': 'custom'
                    })
                    context_id = ContextCoa.search([['id', '=', context_coa_id.id]])
                    new_context = {}
                    new_context.update({
                        'date_from': context_id.date_from,
                        'date_to': context_id.date_to,
                        'state': ctx.get('state'), # context_id.all_entries and 'all' or 'posted',
                        'cash_basis': context_id.cash_basis,
                        'hierarchy_3': context_id.hierarchy_3,
                        'context_id': context_id,
                        'company_ids': context_id.company_ids.ids,
                        'periods_number': context_id.periods_number,
                        'periods': [[context_id.date_from, context_id.date_to]] + context_id.get_cmp_periods(),
                    })
                    coa_lines = CoaReport.with_context(new_context)._lines(line_id=None)
                    rea = [coa for coa in coa_lines if coa.get('id') == acc_brw.id]
                    if rea:
                        columns = rea[0].get('columns')
                        initial = float( (columns and columns[0] or '0.0').replace('$ ', '').replace(',', '') )
                        debit = float( (columns and columns[1] or '0.0').replace('$ ', '').replace(',', '') )
                        credit = float( (columns and columns[1] or '0.0').replace('$ ', '').replace(',', '') )
            else:
                line_used_context = used_context.copy()
                if acc_brw.user_type_id.include_initial_balance == True:
                    initial_date_from = date_from + relativedelta(days=-1)
                    line_used_context['date_from'] = dates['min']
                    line_used_context['date_to'] = initial_date_from
                    line_used_context.pop("strict_range")
                else:
                    initial_date_from = date_from + relativedelta(days=-1)
                    line_used_context['date_to'] = initial_date_from
                    line_used_context['date_from'] = '%s-01-01'%(date_to.year)
                vals = self.with_context(line_used_context)._compute_initial_balance_datas(acc_brw, display_account)
                for val in vals:
                    bal = round(val['balance'], dp)
                    initial += bal
            balance =  initial + debit - credit
            # if acc_brw.code_alias.startswith('1') or acc_brw.code_alias.startswith('5') or acc_brw.code_alias.startswith('6') or acc_brw.code_alias.startswith('7'):
            #     balance = initial - debit - credit # abs(line_total_pre + line.debit - line.credit)
            # elif acc_brw.code_alias.startswith('2') or acc_brw.code_alias.startswith('3') or acc_brw.code_alias.startswith('4'):
            #     balance = initial - debit + credit # abs(line_total_pre - line.debit + line.credit)
        return {
            'initial': initial, 
            'debit': debit, 
            'credit': credit, 
            'balance': balance
        }



class AccountMove(models.Model):
    _inherit = "account.move"

    @api.one
    def _get_tipo_poliza(self):
        tipo = '3'
        for move in self:
            if move.journal_id.type == 'bank':
                if move.journal_id.default_debit_account_id.id != move.journal_id.default_credit_account_id.id:
                    raise except_orm(_('Warning!'),
                        _('La cuenta deudora por defecto y la cuenta acreedora por defecto no son la misma en el diario %s'%move.journal_id.name ))
                if len(move.line_ids) == 2:
                    if move.line_ids[0].account_id.user_type_id.name in ['bank'] and move.line_ids[0].account_id.user_type_id.name in ['bank']:
                        tipo = '3'
                        break
                for line in move.line_ids:
                    if line.account_id.id == move.journal_id.default_debit_account_id.id:
                        if line.debit != 0 and line.credit == 0:
                            tipo = '1'
                            break
                        elif line.debit == 0 and line.credit != 0:
                            tipo = '2'
                            break
            else:
                tipo = '3'
        self.tipo_poliza = tipo
    

    tipo_poliza = fields.Selection([
            ('1','Ingresos'),
            ('2','Egresos'),
            ('3','Diario'),
        ], string="Tipo poliza", 
        compute='_get_tipo_poliza',
        default='3')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    comprobantes_ids = fields.One2many("contabilidad_electronica.comprobante", "move_line_id", 
        string="Comprobantes", ondelete="cascade", oldname="comprobantes")
    comprobantes_cfd_cbb_ids = fields.One2many("contabilidad_electronica.comprobante.otro", "move_line_id", 
        string="Comprobantes (CFD o CBB)", ondelete="cascade", oldname="comprobantes_cfd_cbb")
    comprobantes_ext_ids = fields.One2many("contabilidad_electronica.comprobante.ext", "move_line_id", 
        string="Comprobantes extranjeros", ondelete="cascade", oldname="comprobantes_ext")
    cheques_ids = fields.One2many("contabilidad_electronica.cheque", "move_line_id", 
        string="Cheques", ondelete="cascade", oldname="cheques")
    transferencias_ids = fields.One2many("contabilidad_electronica.transferencia", "move_line_id", 
        string="Transferencias", ondelete="cascade", oldname="transferencias")
    otros_metodos_ids = fields.One2many("contabilidad_electronica.otro.metodo.pago", "move_line_id", 
        string="Otros metodos de pago", ondelete="cascade", oldname="otros_metodos")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: