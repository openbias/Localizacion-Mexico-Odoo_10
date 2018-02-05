# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

class AccountChartReportPDF(models.AbstractModel):
    _name = 'report.bias_coa_hierarchy.accountchart_report_pdf'


    @api.multi
    def data_render(self, data):
        Account = self.env['account.account']
        initial_res = []
        if data.get('is_partner', False):
            acc = Account.with_context(**data).browse(data.get('account_id'))
            acc_id = acc.id
            acc_item = {
                'type': 'view',
                'name': '[%s] %s'%(acc.code, acc.name),
                'initial': acc.initial,
                'debit': acc.debit,
                'credit': acc.credit,
                'balance': acc.balance
            }
            initial_res.append(acc_item)
            if data.get('partner_ids'):
                Partner = self.env['res.partner']
                partner_ids = Partner.with_context(**data).search([('id', 'in', data.get('partner_ids'))])
                total_initial, total_debit, total_credit, total_balance = 0.0, 0.0, 0.0, 0.0
                indx = 0

                for partner in partner_ids:
                    context = data.copy()
                    context['partner_id'] = partner.id
                    account_id = Account.with_context(**context).browse(acc_id)
                    acc_item = {
                        'type': 'normal',
                        'name': partner.name,
                        'initial': account_id.initial,
                        'debit': account_id.debit,
                        'credit': account_id.credit,
                        'balance': account_id.balance
                    }
                    initial_res.append(acc_item)
                    total_initial += account_id.initial or 0.0
                    total_debit += account_id.debit or 0.0
                    total_credit += account_id.credit or 0.0
                    total_balance += account_id.balance or 0.0

                context = data.copy()
                context['not_partner_id'] = True
                account_id = Account.with_context(**context).browse(acc_id)
                if (account_id.initial != 0.0 or account_id.debit != 0.0 or account_id.credit != 0.0 or account_id.balance != 0.0):
                    acc_item = {
                        'type': 'normal',
                        'name': '...',
                        'initial': account_id.initial,
                        'debit': account_id.debit,
                        'credit': account_id.credit,
                        'balance': account_id.balance
                    }
                    initial_res.append(acc_item)
                    total_initial += account_id.initial or 0.0
                    total_debit += account_id.debit or 0.0
                    total_credit += account_id.credit or 0.0
                    total_balance += account_id.balance or 0.0

                acc_item = {
                    'type': 'view',
                    'name': 'Total',
                    'initial': total_initial,
                    'debit': total_debit,
                    'credit': total_credit,
                    'balance': total_balance
                }
                initial_res.append(acc_item)

        else:
            account_ids = Account.with_context(**data).search([('deprecated', '=', False)])
            for acc in account_ids:
                acc_item = {
                    'type': acc.internal_type,
                    'level': acc.level,
                    'code': acc.code,
                    'name': acc.name,
                    'initial': acc.initial,
                    'debit': acc.debit,
                    'credit': acc.credit,
                    'balance': acc.balance
                }
                initial_res.append(acc_item)
        return initial_res


    @api.model
    def render_html(self, docids, data=None):
        context = self.env.context
        model = context.get('active_model')
        active_ids = context.get('active_ids', [])
        Report = self.env['report']
        bias_report = Report._get_report_from_name('bias_coa_hierarchy.accountchart_report_pdf')
        docs = self.env[model].browse(active_ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': bias_report.model,
            'docs': docs,
            'time': time,
            'datas': data['form'],
            'Accounts': self.data_render(data['form'])
        }
        return Report.render('bias_coa_hierarchy.accountchart_report_pdf', docargs)