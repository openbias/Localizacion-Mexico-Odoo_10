# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class AccountChart(models.TransientModel):
    _name = "account.chart"
    _description = "Account chart"

    account_id = fields.Many2one('account.account', 
        string='Account', readonly=False,
        domain=[('deprecated', '=', False)])
    company_id = fields.Many2one('res.company', 
        string='Company', readonly=True, 
        default=lambda self: self.env.user.company_id)
    partner_ids = fields.Many2many('res.partner', 
        string='Partners', required=False)
    journal_ids = fields.Many2many('account.journal', 
        string='Journals', required=True, 
        default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date', default=fields.Date.today())
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
            ('posted', 'All Posted Entries'),
            ('all', 'All Entries')],
        string='Target Moves', required=True, default='all')

    @api.onchange('date_from')
    def onchange_date(self):
        if self.date_from:
            date = datetime.strptime(self.date_from, '%Y-%m-%d')
            self.date_to = date + relativedelta(day=1, months=+1, days=-1)

    def _build_contexts_partner(self, data, result):
        context =  dict(self.env.context)
        if context.get('is_partner', False):
            if not data.get('partner_ids', None):
                acc_ids = self.account_id._get_children_and_consol()
                partner_ids = []
                params = (tuple(acc_ids.ids),)
                query = """SELECT DISTINCT(l.partner_id) AS partner_id  
                    FROM account_move_line l 
                    WHERE 
                        l.account_id in %s"""
                self._cr.execute(query, params)
                for row in self._cr.dictfetchall():
                    partner_ids.append(row['partner_id'])
            else:
                partner_ids = self.partner_ids.ids
            result['partner_ids'] = partner_ids
            result['is_partner'] = True
        return result

    def _build_contexts(self, data):
        context =  dict(self.env.context)
        print "data.get('target_move')", data.get('target_move')
        result = {}        
        result['journal_ids'] = data.get('journal_ids')
        result['state'] = data.get('target_move')
        result['date_from'] = data.get('date_from')
        result['date_to'] = data.get('date_to')
        result['strict_range'] = True if result['date_from'] else False
        result['view_all'] = True
        result['type'] = 'view'
        
        if self.account_id:
            result['account_id'] = self.account_id.id
        result = self._build_contexts_partner(data, result)
        return result


    @api.multi
    def account_chart_open_window(self):
        data = self.read([])[0]
        action_id = self.env.ref('bias_coa_hierarchy.action_account_tree_chart')
        res = {
            'name': action_id.name,
            'type': action_id.type,
            'view_type': action_id.view_mode,
            'view_mode': action_id.view_mode,
            'res_model': action_id.res_model,
            'views': [(action_id.view_id.id, 'tree')],
            'view_id': action_id.view_id.id,
            'target': action_id.target,
            'context': self._build_contexts(data),
            'domain': [('parent_id','=',False), ('type','=','view'), ('deprecated', '=', False)]
        }
        return res

    @api.multi
    def account_chart_open_excel(self):
        data = self.read([])[0]

        context =  dict(self.env.context)
        if context.get('is_partner', False) == True or context.get('is_move', False) == True:
            if not data.get('account_id', None):
                raise UserError(_('Error de Configuración!\nPor favor seleccione una cuenta'))

        ctx = self._build_contexts(data)
        context.update({'active_model': self._name, 'active_ids': [self.id], 'active_id': self.id })
        res = self.env['report'].get_action(self, 'accountchart_report_xlsx', data=ctx)
        return res

    @api.multi
    def account_chart_open_pdf(self):
        self.ensure_one()
        [data] = self.read()
        context =  dict(self.env.context)
        if context.get('is_partner', False) == True or context.get('is_move', False) == True:
            if not data.get('account_id', None):
                raise UserError(_('Error de Configuración!\nPor favor seleccione una cuenta'))

        context.update({'active_model': self._name, 'active_ids': [self.id], 'active_id': self.id })
        ctx = self._build_contexts(data)
        data.update(ctx)
        data.update(context)
        datas = {
            'ids': [],
            'model': 'account.chart',
            'form': ctx
        }
        return self.env['report'].with_context(**context).get_action(self, 'bias_coa_hierarchy.accountchart_report_pdf', data=datas)

    @api.multi
    def account_chart_moves_open_excel(self):
        data = self.read([])[0]
        context =  dict(self.env.context)
        if not data.get('account_id', None):
            raise UserError(_('Error de Configuración!\nPor favor seleccione una cuenta'))

        ctx = self._build_contexts(data)
        context.update({'active_model': self._name, 'active_ids': [self.id], 'active_id': self.id })
        res = self.env['report'].get_action(self, 'accountchartmoves_report_xlsx', data=ctx)
        return res

    @api.multi
    def account_open_pdf(self):
        self.ensure_one()
        [data] = self.read()
        context =  dict(self.env.context)
        if context.get('is_partner', False) == True or context.get('is_move', False) == True:
            if not data.get('account_id', None):
                raise UserError(_('Error de Configuración!\nPor favor seleccione una cuenta'))

        context.update({'active_model': self._name, 'active_ids': [self.id], 'active_id': self.id })
        ctx = self._build_contexts(data)
        data.update(ctx)
        data.update(context)
        datas = {
            'ids': [],
            'model': 'account.chart',
            'form': ctx
        }
        return self.env['report'].with_context(**context).get_action(self, 'accountchartmoves_report_pdf', data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
