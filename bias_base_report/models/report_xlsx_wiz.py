# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.addons.bias_base_report.report.report_xlsx import ReportXlsx


class report_xlsx_wiz(models.TransientModel):
    _name = "report.xlsx.wiz"

    name = fields.Char(string='Name')

    @api.multi
    def action_report_xlsx(self, datas=[], columns=[], report_name="Hoja 1", header=False, freeze_panes=False):
        ctx = {
            'report_name': report_name,
            'datas': datas,
            'header': header,
            'freeze_panes': freeze_panes,
            'columns': columns
        }
        res = self.env['report'].with_context(**ctx).get_action(self, 'report_xlsx', data=ctx)
        return res

class report_xlsx(ReportXlsx):
    _name = 'report.report_xlsx'

    def generate_xlsx_report(self, workbook, data, models):
        company_id = self.env.user.company_id        
        name = data.get('report_name', 'Hoja 1')
        header = data.get('header', False)
        freeze_panes = data.get('freeze_panes', False)
        datas = data.get('datas', [])
        columns = data.get('columns', [])

        worksheet = workbook.add_worksheet( name )
        worksheet.hide_gridlines(2)

        title_company = workbook.add_format({
            'font_name':'Arial', 
            'font_size':18, 'bold':1, 'align':'center', 
            'valign':'vcenter', 'color':'#032C46'
        })
        header_format = workbook.add_format({
            'font_name':'Arial', 'font_size':12, 'bold':1, 'italic':0, 
            'align':'center', 'valign':'vcenter', 'fg_color':'#AAAAAA', 
            'color':'#FFFFFF', 'bottom': 2, 'bottom_color':'#AAAAAA', 
            'top': 2, 'top_color':'#AAAAAA'
        })
        money_format = workbook.add_format({
            'font_name':'Trebuchet MS', 'font_size':10, 'align':'left', 
            'valign':'vcenter', 'num_format':'$#,##0.00;[RED]-$#,##0.00', 
            'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'
        })
        string_format = workbook.add_format({
            'font_name':'Trebuchet MS', 'font_size':10, 'align':'left', 
            'valign':'vcenter', 'fg_color':'#F2F2F2', 'bottom': 4, 
            'bottom_color':'#D9D9D9'
        })
        for column in columns:
            if len(column) == 2:
                worksheet.set_column(column[0], column[1])

        row = 1
        if header:
            worksheet.merge_range('A1:F1', company_id.name, title_company)
            worksheet.merge_range('A3:F3', name, title_company)
            row = 5
        
        if len(datas):
            worksheet.freeze_panes(row, 0)
            header = datas[0]
            worksheet.write_row('A%s'%(row), header, header_format)
            row += 1

            for d in datas[1:]:
                worksheet.write_row('A%s'%(row), d, money_format)
                row += 1

        company_id = self.env.user.company_id
report_xlsx('report.report_xlsx', 'report.xlsx.wiz')