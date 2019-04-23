# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _

from openerp.addons.bias_base_report.report.report_xlsx import ReportXlsx

class AccountChartMovesReportXlsx(ReportXlsx):
    _name = 'report.accountchartmoves_report_xlsx'

    def generate_xlsx_report(self, workbook, data, models):
        company_id = self.env.user.company_id        
        workbook.set_properties({
            'title': _('Account Chart'),
            'subject': _('Account Chart'),
            'author': 'OpenBias',
            'manager': 'Odoo',
            'company': company_id.name,
            'category': 'Reportes Financieros',
            'comments': 'Reportes Financieros'
        })

        title_company = workbook.add_format({'font_name':'Arial', 'font_size':18, 'bold':1, 'align':'center', 'valign':'vcenter', 'color':'#032C46'})
        header_format = workbook.add_format({'font_name':'Arial', 'font_size':12, 'bold':1, 'italic':0, 'align':'center', 'valign':'vcenter', 'fg_color':'#AAAAAA', 'color':'#FFFFFF', 'bottom': 2, 'bottom_color':'#AAAAAA', 'top': 2, 'top_color':'#AAAAAA' })
        string_format = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'align':'left', 'valign':'vcenter', 'fg_color':'#F2F2F2', 'bottom': 4, 'bottom_color':'#D9D9D9'})
        string_format_01 = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'bold':1, 'align':'left', 'valign':'vcenter', 'fg_color':'#F2F2F2', 'bottom': 4, 'bottom_color':'#D9D9D9'})
        string_format_02 = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'align':'left', 'valign':'vcenter', 'fg_color':'#FFFFFF', 'bottom': 4, 'bottom_color':'#D9D9D9'})
        string_format_03 = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'align':'left', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9', 'color': 'blue'})
        money_format = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'$#,##0.00;[RED]-$#,##0.00', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'})
        money_format_01 = workbook.add_format({'font_name':'Trebuchet MS', 'font_size':10, 'bold':1, 'align':'right', 'valign':'vcenter', 'num_format':'$#,##0.00;[RED]-$#,##0.00', 'fg_color':'#F2F2F2', 'bottom': 4, 'bottom_color':'#D9D9D9'})

        for obj in models:
            data = obj.read([])[0]
            ctx = obj._build_contexts(data)

            # One sheet by
            sheet = workbook.add_worksheet( _('Account Chart') )
            sheet.hide_gridlines(2)
            sheet.freeze_panes(8, 0)

            target_move = _('Todas las Entradas')
            if ctx['state'] == 'all':
                target_move = _('Todas las Entradas')
            elif ctx['state'] == 'posted':
                target_move = _('Todas las Entradas Posteadas')

            #header
            sheet.set_column('A:A', 35)
            sheet.set_column('B:G', 15)
            sheet.merge_range('A1:F1', company_id.name, title_company)
            sheet.merge_range('A3:F3', _('Auxiliar de Cuentas '), title_company)
            sheet.write_string(4, 1, _('Movimientos:'), string_format_01)            
            sheet.write_string(4, 3, _('Fecha Inicial :'), string_format_01)
            sheet.write_string(5, 3, _('Fecha Final :'), string_format_01)

            sheet.write_string(4, 2, target_move, string_format_02)
            sheet.write_string(4, 4, ctx['date_from'], string_format_02)
            sheet.write_string(5, 4, ctx['date_to'], string_format_02)



            Account = self.env['account.account']
            acc = Account.with_context(**ctx).browse(ctx.get('account_id'))
            acc_ids = acc._get_children_and_consol()

            h_balance = ['Cliente', 'Factura', 'Referencia', _('Fecha'), _('Debito'), _('Credito'), ' ']
            sheet.write_row('A8', h_balance, header_format)
            # Start from the first cell below the headers.
            row = 8
            col = 0
            acc_id = acc.id
            sheet.write_string(row, col, '[%s] %s'%(acc.code, acc.name), string_format_01)
            sheet.write_string(row, col + 1, ' ', string_format_01)
            sheet.write_string(row, col + 2, ' ', string_format_01)
            sheet.write_number(row, col + 3, acc.initial, money_format_01)
            sheet.write_number(row, col + 4, acc.debit, money_format_01)
            sheet.write_number(row, col + 5, acc.credit, money_format_01)
            sheet.write_number(row, col + 6, acc.balance, money_format_01)
            row += 1


            # Busca lineas de asientos
            Move = self.env['account.move']
            Line = self.env['account.move.line']
            where = [('account_id', 'in', acc_ids.ids), ('date', '<=', ctx['date_to']), ('date', '>=', ctx['date_from'])]
            if ctx.get('state') and ctx.get('state').lower() != 'all':
                where += [('move_id.state', '=', ctx.get('state'))]
            line_ids = Line.search(where)
            total_debit, total_credit = 0.0, 0.0
            for aml in line_ids:
                ref = ''
                partner = ''

                # domain account.move(4286,) [('id', 'in', [])]
                ref = aml.move_id.name or aml.move_id.ref or ''
                partner = aml.move_id.partner_id and aml.move_id.partner_id.name or ''
                if not partner:
                    action = aml.move_id.open_cash_basis_view()
                    domain = action.get('domain', [])

                    for move in Move.search(domain):
                        if move.tipo_poliza == '3' and move.partner_id:
                            ref = move.name or move.ref or ''
                            partner = move.partner_id and move.partner_id.name or ''
                            break

                sheet.write_string(row, col, '%s'%(partner), string_format_03)
                sheet.write_string(row, col + 1, '%s'%(ref), string_format_03)
                sheet.write_string(row, col + 2, '%s'%(aml.move_id.name or aml.move_id.ref or ''), string_format_03)
                sheet.write_string(row, col + 3, aml.date, string_format_02)
                sheet.write_number(row, col + 4, aml.debit, money_format)
                sheet.write_number(row, col + 5, aml.credit, money_format)
                sheet.write_string(row, col + 6, ' ', string_format_02)
                row += 1

                total_debit += aml.debit or 0.0
                total_credit += aml.credit or 0.0

            sheet.write_string(row, col, ' ', string_format_03)
            sheet.write_string(row, col + 1, ' ', string_format_03)
            sheet.write_string(row, col + 2, ' ', string_format_03)
            sheet.write_string(row, col + 3, 'Total', string_format_03)
            sheet.write_number(row, col + 4, total_debit, money_format)
            sheet.write_number(row, col + 5, total_credit, money_format)
            sheet.write_string(row, col + 6, ' ', string_format_02)


AccountChartMovesReportXlsx('report.accountchartmoves_report_xlsx', 'account.chart')