# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRuleGroup(models.Model):
    _name = "hr.salary.rule.group"
    
    name = fields.Char(string="Nombre", required=True)
    
class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    tipo_id = fields.Many2one('cfdi_nomina.tipo', string=u"Tipo")
    tipo_horas_id = fields.Many2one("cfdi_nomina.tipo_horas", string="Tipo horas extras")
    gravado_o_exento = fields.Selection([
                ('gravado','Gravado'), 
                ('exento','Exento'),
                ('ninguno', 'Ninguno')], 
            string="Gravado o exento", required=True, default="gravado")
    codigo_agrupador_id = fields.Many2one('cfdi_nomina.codigo_agrupador', string=u"Código Agrupador")
    agrupacion_id = fields.Many2one('hr.salary.rule.group', string='Agrupacion')
    appears_on_payslip_report = fields.Boolean('Appears on Payslip Report', default=False, help="Used to display the salary rule on payslip report.")
    appears_on_payslip_xlsx = fields.Boolean('Appears on Report XLSX', default=False, help="Used to display the salary rule on payslip report.")

    @api.onchange('codigo_agrupador_id')
    def _onchange_codigo_agrupador_id(self):
        if self.codigo_agrupador_id:
            tipo_id = self.codigo_agrupador_id.tipo_id
        return

    #TODO should add some checks on the type of result (should be float)
    @api.multi
    def compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(safe_eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).') % (self.name, self.code))
        else:
            context = dict(self.env.context)
            """
            localdict.update({'gravado': 0.0, 'exento': 0.0, 'this': self, "UserError": UserError, 'time': time, 'datetime': datetime, 'timedelta': timedelta, 'ValidationError': ValidationError })
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            cfdi_nomina = {'gravado': localdict['gravado'], 'exento': localdict['exento']}
            context.setdefault('cfdi_nomina', {})[self.id] = cfdi_nomina
            print localdict
            print 'result_qty' in localdict and localdict['result_qty'] or 1.0
            print 'result_rate' in localdict and localdict['result_rate'] or 100.0
            """
            localdict.update({'gravado': 0.0, 'exento': 0.0, 'this': self, "UserError": UserError, 'time': time, 'datetime': datetime, 'timedelta': timedelta, 'relativedelta': relativedelta, 'ValidationError': ValidationError })
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            try:
                cfdi_nomina = {'gravado': localdict.get("gravado"), 'exento': localdict.get("exento")}
                context.setdefault('cfdi_nomina', {})[self.id] = cfdi_nomina
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            except:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))


class HrContract(models.Model):
    _inherit = "hr.contract"

    regimen_contratacion_id = fields.Many2one('cfdi_nomina.regimen_contratacion', string=u"Régimen Contratación")
    periodicidad_pago_id = fields.Many2one("cfdi_nomina.periodicidad_pago", string=u"Periodicidad pago")
    is_cfdi = fields.Boolean(default=True, string="Es CFDI?")

class HrContractType(models.Model):
    _inherit = "hr.contract.type"
    _name = "hr.contract.type"
    _description = "Tipo Contrato"

    code = fields.Char(string=u"Código Catálogo SAT", required=True, default='')

class HrJob(models.Model):
    _inherit = "hr.job"

    riesgo_puesto_id = fields.Many2one("cfdi_nomina.riesgo_puesto", string="Clase riesgo")


