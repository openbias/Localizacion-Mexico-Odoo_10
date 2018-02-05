# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

import xml.etree.ElementTree as ET

class ReporteAcumulado(models.TransientModel):
    _name = "cfdi_nomina.reporte_acumulado"

    fecha_inicio = fields.Date(string="Fecha inicio", required=True)
    fecha_fin = fields.Date(string="Fecha fin", required=True)
    nomina_ids = fields.Many2many("hr.payslip.run", string=u"Nóminas", required=True)
    rule_ids = fields.Many2many("hr.salary.rule", string="Reglas") #ya no se usará, ahora es por agrupación
    rule_group_ids = fields.Many2many("hr.salary.rule.group", string="Agrupaciones")
    employee_ids = fields.Many2many("hr.employee", string="Empleados")
    datas = fields.Binary(string="Reporte CSV")
    fname = fields.Char(string="Fname")

    @api.multi
    def action_reporte_acumulado(self):
        data, line_ids = self._create_report()
        view_id = self.env['ir.model.data'].get_object('cfdi_nomina', 'reporte_acumulado_line_view').id    
        return {
            'name': 'Reporte del periodo %s a %s'%(self.fecha_inicio, self.fecha_fin),
            'type': 'ir.actions.act_window',
            'res_model': "cfdi_nomina.reporte.acumulado.line",
            'view_type': "form",
            'view_mode': 'list',
            'context': self._context,
            'view_id': view_id,
            'domain': [('id', 'in', line_ids)]
        }

    @api.multi
    def action_reporte_excel(self):
        for this in self:
            data, line_ids = self._create_report()
            header = ["Empleado", "Cod. Emp.", "RFC", "IMSS"]
            for rule in this.rule_group_ids:
                header.append(rule.name)
            header.extend(["Otras percepciones", "Otras deducciones", "Gravado", "Exento", "Neto"])
            rows = []
            employee_obj = self.env['hr.employee']
            for line in data:
                name = employee_obj.browse(line["employee_id"]).nombre_completo
                row = [name, line["codemp"], line["rfc"], line["imss"]]
                for rule in this.rule_group_ids:
                    row.append(line.get("rule_group_%s"%rule.id, 0))
                row.extend([line["p_otras"], line["d_otras"], line["gravado"], line["exento"], line["neto"]])
                rows.append(row)
            csv_data = ",".join(header) + "\n"
            for row in rows:
                _row = []
                for x in row:
                    if type(x) != unicode and type(x) != str:
                        _row.append(str(x))
                    else:
                        _row.append(x)
                csv_data += ",".join([x.replace(",", " ") for x in _row]) + "\n"
            datas = base64.b64encode(csv_data.encode("utf-8"))
            this.write({'datas': datas, 'fname': 'Reporte acumulados %s al %s.csv'%(this.fecha_inicio, this.fecha_fin)})
            return {
                'name': 'Reporte acumulados',
                'type': 'ir.actions.act_window',
                'res_model': "cfdi_nomina.reporte.acumulado",
                'view_type': "form",
                'view_mode': 'form',
                'context': self._context,
                'res_id': this.id,
                'target': 'new'
            }

    @api.multi
    def _create_report(self):
        context = self._context
        line_ids = []
        data = []
        for this in self:

            if not this.nomina_ids:
                raise UserError(u"No se han seleccionado nóminas")
                
            # rule_ids = [x.id for x in this.rule_group_ids]
            rule_ids = this.rule_group_ids
            context["rule_ids"] = rule_ids.ids
            
            employee_obj = self.env['hr.employee']
            slip_line_obj = self.env['hr.payslip.line']
            model_obj = self.env['ir.model.data']

            PERCEPCION = model_obj.get_object("cfdi_nomina", "catalogo_tipo_percepcion").id
            DEDUCCION = model_obj.get_object("cfdi_nomina", "catalogo_tipo_deduccion").id
            HORA_EXTRA = model_obj.get_object("cfdi_nomina", "catalogo_tipo_hora_extra").id
            INCAPACIDAD = model_obj.get_object("cfdi_nomina", "catalogo_tipo_incapacidad").id

            if this.employee_ids:
                employee_ids = this.employee_ids
            else:
                employee_ids = employee_obj.search([])

            line_obj = self.env['cfdi_nomina.reporte_acumulado_line']
            line_ids = []
            data = []

            for employee in employee_ids:
                vals = {
                    'employee_id': employee.id,
                    'codemp': employee.cod_emp,
                    'rfc': employee.rfc,
                    'imss': employee.imss,
                }
                slip_line_ids = slip_line_obj.search([
                    ('slip_id.payslip_run_id', 'in', this.nomina_ids ),
                    ('employee_id', '=', employee.id)
                ])
                if not slip_line_ids:
                    if len(this.employee_ids.ids) > 0:
                        raise UserError(u"El empleado %s no está en las nóminas seleccionadas"%employee.nombre_completo)
                    else:
                        continue
                neto = 0
                p_otras = 0
                d_otras = 0
                gravado = 0
                exento = 0
                rule_totals = {rid: 0 for rid in rule_ids.ids}
                for slip_line in slip_line_ids:
                    tipo = slip_line.salary_rule_id.gravado_o_exento or 'gravado'
                    if tipo == 'gravado':
                        gravado += slip_line.total
                    elif tipo == 'exento':
                        exento += slip_line.total
                    if slip_line.salary_rule_id.tipo_id.id in (PERCEPCION, HORA_EXTRA):
                        neto += slip_line.total
                    if slip_line.salary_rule_id.tipo_id.id in (DEDUCCION, INCAPACIDAD):
                        neto -= slip_line.total
                    if slip_line.salary_rule_id.agrupacion_id.id in rule_ids:
                        rule_totals[slip_line.salary_rule_id.agrupacion_id.id] += slip_line.total
                        #vals.update({
                        #    "rule_group_%s"%slip_line.salary_rule_id.agrupacion_id.id: slip_line.total
                        #})
                    else:
                        if slip_line.salary_rule_id.tipo_id.id in (PERCEPCION, HORA_EXTRA):
                            p_otras += slip_line.total
                        elif slip_line.salary_rule_id.tipo_id.id in (DEDUCCION, INCAPACIDAD):
                            d_otras += slip_line.total

                for rule_id,rule_total in rule_totals.iteritems():
                    vals.update({"rule_group_%s"%rule_id: rule_total})
                    
                vals.update({
                    'neto': neto,
                    'p_otras': p_otras,
                    'd_otras': d_otras,
                    'exento': exento,
                    'gravado': gravado
                })
                data.append(vals)
                line_id = line_obj.create(vals)
                line_ids.append(line_id.id)

        return data, line_ids


class ReporteAcumuladoLine(models.TransientModel):
    _name = "cfdi_nomina.reporte_acumulado_line"
    
    employee_id = fields.Many2one("hr.employee", string="Empleado")
    codemp = fields.Integer("Cod. Emp.")
    rfc = fields.Char("RFC")
    imss = fields.Char("IMSS")
    p_otras = fields.Float("Otras percepiones")
    d_otras = fields.Float("Otras deducciones")
    gravado = fields.Float("Total gravado")
    exento = fields.Float("Total exento")
    neto = fields.Float("Neto")

    # @api.model_cr
    # def init(self):
    #     #Columnas por regla (ya no se usarán)
    #     self.env.cr.execute("select id from hr_salary_rule")
    #     for row in self.env.cr.fetchall():
    #         field_name = "rule_%s"%row[0]
    #         self.columns[field_name] = fields.Float(field_name)
    #     #Columnas por agrupación
    #     self.env.cr.execute("select id from hr_salary_rule_group")
    #     for row in self.env.cr.fetchall():
    #         field_name = "rule_group_%s"%row[0]
    #         self.columns[field_name] = fields.Float(field_name)
    #     return super(ReporteAcumuladoLine, self).init()

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     context = self._context
    #     res = super(ReporteAcumuladoLine, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type != "tree":
    #         return res
    #     arch = res["arch"]
    #     root = ET.fromstring(arch)
    #     if 'rule_ids' in context:
    #         for rule in self.env['hr.salary.rule.group'].browse(context["rule_ids"]):
    #             root.insert(4,ET.XML('<field name="rule_group_%s" string="%s" sum="Total"/>'%(rule.id, rule.name.encode("utf-8"))))
    #     res["arch"] = ET.tostring(root, encoding="UTF-8")
    #     return res