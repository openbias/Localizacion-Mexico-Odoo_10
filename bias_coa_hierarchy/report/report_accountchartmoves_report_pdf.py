# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.addons.bias_base_report.report.report_xlsx import ReportXlsx

class AccountChartMovesReportPDF(models.AbstractModel):
    _name = 'report.accountchartmoves_report_pdf'

    @api.multi
    def data_render(self, data):
        initial_res = []
        
        Account = self.env['account.account']
        Move = self.env['account.move']
        Line = self.env['account.move.line']
        
        acc = Account.with_context(**data).browse(data.get('account_id'))
        acc_ids = acc._get_children_and_consol()

        for acc_id in acc:
            acc_item = {
                'type': 'view',
                'partner': '',
                'name': '[%s] %s '%(acc_id.code, acc_id.name),
                'ref': '',                
                'initial': acc_id.initial,
                'debit': acc_id.debit,
                'credit': acc_id.credit,
                'balance': acc_id.balance,
                'date': ''
            }
            initial_res.append(acc_item)
        
        # Busca lineas de asientos
        where = [('account_id', 'in', acc_ids.ids), ('date', '<=', data['date_to']), ('date', '>=', data['date_from'])]
        line_ids = Line.search(where)
        total_debit, total_credit = 0.0, 0.0
        for aml in line_ids:
            ref = ''
            partner = ''

            # domain account.move(4286,) [('id', 'in', [])]
            ref = aml.move_id.name or aml.move_id.ref or ''
            partner = aml.move_id.partner_id and aml.move_id.partner_id.name or None
            if not partner:
                action = aml.move_id.open_cash_basis_view()
                domain = action.get('domain', [])
                for move in Move.search(domain):
                    if move.tipo_poliza == '3':
                        ref = move.name or move.ref or ''
                        partner = move.partner_id and move.partner_id.name or ''

            acc_item = {
                'type': 'normal',
                'partner': partner,
                'ref': ref,
                'name': aml.move_id.name or aml.move_id.ref or '',
                'initial': 0.0,
                'debit': aml.debit,
                'credit': aml.credit,
                'balance': 0.0,
                'date': '%s'%(aml.date)
            }
            initial_res.append(acc_item)
            total_debit += aml.debit or 0.0
            total_credit += aml.credit or 0.0
        acc_item = {
            'type': 'view',
            'partner': '',
            'ref': '',
            'name': 'Total',
            'initial': acc_id.initial,
            'debit': total_debit,
            'credit': total_credit,
            'balance': acc_id.balance,
            'date': ''
        }
        initial_res.append(acc_item)

        return initial_res

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': self.data_render(data.get('form')),
        }
        return self.env['report'].render('bias_coa_hierarchy.accountchartmoves_report_pdf', docargs)