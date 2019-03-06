# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, registry, _
import logging
import textwrap

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ['mail.thread', 'hr.payslip']

    ##############################
    #
    # Reporte PDF Nomina
    #
    ##############################
    @api.multi
    def get_dias_trabajados(self):
        dias = self._get_days("WORK100")
        res = 0
        if dias:
            res = dias[0]
        return res

    def get_info_sat(self, splitme):
        pp = textwrap.wrap(splitme, width=120)
        export_text = ""
        for p in pp:
            export_text += p + '\n'
        return export_text

    def get_periodo(self):
        return '%s a %s'%(self.date_from, self.date_to)

    def get_message(self):
        msg = "RECIBI DE LA EMPRESA %s LA CANTIDAD DE %s \
        MISMAS QUE CUBREN LAS PERCEPCIONES QUE ME CORRESPONDEN EN EL PERIODO INDICADO, \
        NO EXISTIENDO NINGUN ADEUDO, POR PARTE DE LA EMPRESA PARA EL SUSCRITO, \
        PUES ESTOY TOTALMENTE PAGADO DE MIS SALARIOS Y PRESTACIONES DEVENGADAS HASTA LA FECHA."%(self.company_id.name, self.cant_letra.upper())
        return msg

    def get_other_lines_type(self):
        datas = []
        for indx in range(0, 3):
            datas_tmp = {
                'p_code': ' ',
                'p_name': ' ',
                'p_total': None,
                'd_code': ' ',
                'd_name': ' ',
                'd_total': None,
            }
            datas.append(datas_tmp)
        return datas

    def get_lines_reportcode(self, code):
        datas_tmp = {
            'code': ' ',
            'name': ' ',
            'codesat': ' ',
            'namesat': ' ',
            'quantity': 0.0,
            'amount': 0.0,
            'total': 0.0,
        }
        line = self.line_ids.filtered(lambda r: r.code == code and r.salary_rule_id.appears_on_payslip_report == True)
        if line:
            p_codigo_id = line and line.salary_rule_id or None
            if p_codigo_id:
                datas_tmp['code'] = p_codigo_id and p_codigo_id.code or ' '
                datas_tmp['name'] = p_codigo_id and p_codigo_id.name or ' '
                datas_tmp['codesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.code or ' '
                datas_tmp['namesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.name or ' '
            datas_tmp['quantity'] = line and line.quantity or 0.0
            datas_tmp['amount'] = line and line.amount or 0.0
            datas_tmp['total'] = line and line.total or 0.0
        print "code=", code, datas_tmp
        return datas_tmp

    def _get_lines_type(self, ttype):
        Model = self.env['ir.model.data']
        line_ids = self.line_ids
        tipos = {
            'p': Model.get_object("cfdi_nomina", "catalogo_tipo_percepcion").id,
            'd': Model.get_object("cfdi_nomina", "catalogo_tipo_deduccion").id,
            'h': Model.get_object("cfdi_nomina", "catalogo_tipo_hora_extra").id,
            'i': Model.get_object("cfdi_nomina", "catalogo_tipo_incapacidad").id,
            'o': Model.get_object("cfdi_nomina", "catalogo_tipo_otro_pago").id
        }
        lines = self.line_ids.filtered(lambda r: r.salary_rule_id.tipo_id.id == tipos[ttype] and r.salary_rule_id.appears_on_payslip_report == True)
        return lines

    def get_lines_o(self):
        datas = []
        p_lines = self._get_lines_type('o')
        d_lines = []
        len_criteria = len(p_lines)
        if len(p_lines) < len(d_lines):
            len_criteria = len(d_lines)
        payslip_tmp = {
            'p_code': ' ',
            'p_name': ' ',
            'p_codesat': ' ',
            'p_namesat': ' ',
            'p_total': 0.0,
            'd_code': ' ',
            'd_name': ' ',
            'd_codesat': ' ',
            'd_namesat': ' ',
            'd_total': 0.0,
        }
        for indx in range(0, len_criteria):
            p_line = p_lines[indx] if len(p_lines) > indx else None
            d_line = d_lines[indx] if len(d_lines) > indx else None
            datas_tmp = payslip_tmp.copy()
            p_codigo_id = p_line and p_line.salary_rule_id or None
            if p_codigo_id:
                datas_tmp['p_code'] = p_codigo_id and p_codigo_id.code or ' '
                datas_tmp['p_name'] = p_codigo_id and p_codigo_id.name or ' '
                datas_tmp['p_codesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.code or ' '
                datas_tmp['p_namesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.name or ' '
            datas_tmp['p_total'] = p_line and p_line.total or 0.0
            d_codigo_id = d_line and d_line.salary_rule_id or None
            if d_codigo_id:
                datas_tmp['d_code'] = d_codigo_id and d_codigo_id.code or ' '
                datas_tmp['d_name'] = d_codigo_id and d_codigo_id.name or ' '
                datas_tmp['d_codesat'] = d_codigo_id and d_codigo_id.codigo_agrupador_id and d_codigo_id.codigo_agrupador_id.code or ' '
                datas_tmp['d_namesat'] = d_codigo_id and d_codigo_id.codigo_agrupador_id and d_codigo_id.codigo_agrupador_id.name or ' '
            datas_tmp['d_total'] = d_line and d_line.total or 0.0
            datas.append(datas_tmp)
        if len(datas) == 0:
            for i in range(4):
                datas_tmp = payslip_tmp.copy()
                datas.append(datas_tmp)
        else:
            for i in range(2):
                datas_tmp = payslip_tmp.copy()
                datas.append(datas_tmp)
        return datas

    def get_lines_dp(self):
        datas = []
        p_lines = self._get_lines_type('p')
        d_lines = self._get_lines_type('d')
        len_criteria = len(p_lines)
        if len(p_lines) < len(d_lines):
            len_criteria = len(d_lines)
        payslip_tmp = {
            'p_code': ' ',
            'p_name': ' ',
            'p_codesat': ' ',
            'p_namesat': ' ',
            'p_total': 0.0,
            'd_code': ' ',
            'd_name': ' ',
            'd_codesat': ' ',
            'd_namesat': ' ',
            'd_total': 0.0,
        }
        for indx in range(0, len_criteria):
            p_line = p_lines[indx] if len(p_lines) > indx else None
            d_line = d_lines[indx] if len(d_lines) > indx else None
            datas_tmp = payslip_tmp.copy()

            p_codigo_id = p_line and p_line.salary_rule_id or None
            if p_codigo_id:
                datas_tmp['p_code'] = p_codigo_id and p_codigo_id.code or ' '
                datas_tmp['p_name'] = p_codigo_id and p_codigo_id.name or ' '
                datas_tmp['p_codesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.code or ' '
                datas_tmp['p_namesat'] = p_codigo_id and p_codigo_id.codigo_agrupador_id and p_codigo_id.codigo_agrupador_id.name or ' '
            datas_tmp['p_total'] = p_line and p_line.total or 0.0
            d_codigo_id = d_line and d_line.salary_rule_id or None
            if d_codigo_id:
                datas_tmp['d_code'] = d_codigo_id and d_codigo_id.code or ' '
                datas_tmp['d_name'] = d_codigo_id and d_codigo_id.name or ' '
                datas_tmp['d_codesat'] = d_codigo_id and d_codigo_id.codigo_agrupador_id and d_codigo_id.codigo_agrupador_id.code or ' '
                datas_tmp['d_namesat'] = d_codigo_id and d_codigo_id.codigo_agrupador_id and d_codigo_id.codigo_agrupador_id.name or ' '
            datas_tmp['d_total'] = d_line and d_line.total or 0.0
            datas.append(datas_tmp)
        if len(datas) == 0:
            for i in range(4):
                datas_tmp = payslip_tmp.copy()
                datas.append(datas_tmp)
        else:
            for i in range(2):
                datas_tmp = payslip_tmp.copy()
                datas.append(datas_tmp)
        return datas
    ##############################
    #
    # FIN Reporte PDF Nomina
    #
    ##############################