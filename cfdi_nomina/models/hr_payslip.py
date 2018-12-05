# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, tools, _, registry
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval
from odoo.api import Environment
from openerp.addons.bias_base_report.bias_utis.amount_to_text_es_MX import amount_to_text

import re
import pytz
from pytz import timezone
from datetime import datetime, date
from dateutil import relativedelta
import tempfile
import os
import inspect
import textwrap

import logging
import threading
import base64

logging.basicConfig(level=logging.INFO)


def extraeDecimales(nNumero, max_digits=2):
    strDecimales = str( round(nNumero%1, 2) ).replace('0.','')
    strDecimales += "0"*max_digits
    strDecimales = strDecimales[0:max_digits]
    return long( strDecimales )

def cant_letra(currency, amount):
    if currency.name == 'COP':
        nombre = currency.nombre_largo or 'M/CTE'
        siglas = 'M/CTE'
        nNumero = round( amount , 2)
        decimales = extraeDecimales(nNumero, 2)
        am = str(nNumero).split('.')
        n_entero = amount_to_text().amount_to_text_cheque(float(am[0]), nombre, "").replace("  ", "").replace("00/100", "")
        n_decimales = amount_to_text().amount_to_text_cheque(float(decimales), 'centavos', siglas).replace("00/100 ", "")
        name = "%s con %s "%(n_entero, n_decimales)
    else:
        nombre = currency.nombre_largo or ''
        siglas = currency.name
        name = amount_to_text().amount_to_text_cheque(float(amount), nombre, siglas).capitalize()
    return name



CATALOGO_TIPONOMINA = [('O','Ordinaria'),('E','Extraordinaria')]

class HrPayslipEmployees(models.TransientModel):
    _inherit ='hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        context = dict(self._context)
        res = super(HrPayslipEmployees, self).compute_sheet()
        if context.get('active_id', False):
            self.env['hr.payslip.run'].browse([context['active_id']]).compute_sheet_run_line()


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ['mail.thread', 'hr.payslip.run']
    _description = 'Payslip Batches'
    _order = "date_start desc"


    @api.model
    def _default_currency(self):
        currency_id = self.env.user.company_id.currency_id
        return currency_id

    @api.one
    @api.depends('slip_ids', 'slip_ids.state', 'slip_ids.timbrada')
    def _compute_state(self):
        eval_state = True if self.eval_state else False
        state = 'draft'
        if len(self.slip_ids) == 0:
            state = 'draft'
        elif any(slip.state == 'draft' for slip in self.slip_ids):  # TDE FIXME: should be all ?
            state = 'draft'
        elif all(slip.state in ['cancel', 'done'] for slip in self.slip_ids):
            state = 'close'
        else:
            state = 'draft'
        self.state = state
        return True

    @api.one
    @api.depends('slip_ids', 'source_sncf', 'amount_sncf')
    def _compute_sncf(self):
        self.es_sncf = True if self.source_sncf else False
        for line in self.sudo().slip_ids:
            line.source_sncf = self.source_sncf
            line.amount_sncf = self.amount_sncf
        return True

    @api.one
    @api.depends('fecha_pago', 'concepto', 'slip_ids', 'slip_ids.total')
    def _compute_total_payslip(self):
        if not self.slip_ids:
            self.total = 0.0
        else:
            self.sudo().slip_ids.write({
                    'fecha_pago': self.fecha_pago, 
                    'concepto': self.concepto,
                    'source_sncf': self.source_sncf,
                    'amount_sncf': self.amount_sncf })
            p_total = 0.0
            for line in self.sudo().slip_ids:
                p_total += line.total
            self.total = p_total
        return True


    currency_id = fields.Many2one('res.currency', string='Currency',
            required=True, readonly=True, 
            default=_default_currency, track_visibility='always')
    total = fields.Monetary(string="Total Amount", copy=False, store=True, compute='_compute_total_payslip')

    es_sncf = fields.Boolean(string='Entidad SNCF', readonly=True, compute='_compute_sncf')
    source_sncf = fields.Selection([
            ('IP', 'Ingresos propios'),
            ('IF', 'Ingreso federales'),
            ('IM', 'Ingresos mixtos')],
        string="Recurso Entidad SNCF")
    amount_sncf = fields.Monetary(string="Monto Recurso SNCF")
    eval_state = fields.Boolean('Eval State', compute='_compute_state')
    fecha_pago = fields.Date(string="Fecha pago", required=True)
    concepto = fields.Char(string="Concepto", required=True)

    def _confirm_sheet_run_date(self):
        ids = self.ids
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            tz = self.env.user.tz or "UTC"
            hora_factura_utc = datetime.now(timezone("UTC"))
            dtz = hora_factura_utc.astimezone(timezone(tz)).strftime("%Y-%m-%d %H:%M:%S")
            dtz = dtz.replace(" ", "T")

            Payslip = self.sudo().env['hr.payslip.run']
            Slip = self.sudo().env['hr.payslip']
            for run in Payslip.browse(ids):
                for slip_id in run.slip_ids:
                    if not slip_id.date_invoice_cfdi:
                        logging.info('---DATE %s '%(dtz) )
                        slip_id.write({'date_invoice_cfdi': dtz})
                        # new_cr.execute("UPDATE hr_payslip SET date_invoice_cfdi='%s' WHERE id=%s "%(dtz, slip_id.id) )
                        new_cr.commit()
            new_cr.close()
        return {}

    def _confirm_sheet_run_calculation(self):
        ids = self.ids
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            
            Payslip = self.sudo().env['hr.payslip.run']
            Slip = self.sudo().env['hr.payslip']
            for run in Payslip.browse(ids):
                for slip_id in run.slip_ids:
                    if slip_id.uuid and slip_id.state not in ['draft']:
                        pass
                    logging.info("Confirm Sheet Run Payslip %s 00 ---- "%(slip_id.id,))
                    # slip_id.with_context(batch=True)._calculation_confirm_sheet([slip_id.id], use_new_cursor=new_cr.dbname)
                    Slip.with_context(batch=True)._calculation_confirm_sheet([slip_id.id], use_new_cursor=new_cr.dbname)
                    new_cr.commit()
            new_cr.close()
        return {}


    def _confirm_sheet_run_message(self):
        ids = self.ids
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            msg = ''
            Payslip = self.sudo().env['hr.payslip.run']
            for run in Payslip.browse(ids):
                for slip_id in run.slip_ids:
                    if slip_id.mensaje_validar:
                        msg += "<b>Error Nomina %s</b><br />"%(slip_id.number)
                        msg += "<ol>%s</ol><br/>"%(slip_id.mensaje_validar)
                    elif slip_id.mensaje_timbrado_pac:
                        msg += "<b>Mensaje TIMBRAR PAC %s</b><br />"%(slip_id.number)
                        msg += "<ul>%s</ul>"%(slip_id.mensaje_timbrado_pac)
                    elif slip_id.mensaje_pac:
                        msg += "<b>Mensaje CANCELAR PAC %s</b><br />"%(slip_id.number)
                        msg += "<ul>%s</ul>"%(slip_id.mensaje_validar)
                if len(msg) != 0:
                    run.message_post(body=msg)
            new_cr.commit()
            new_cr.close()
        return {}

    @api.multi
    def confirm_sheet_run(self):
        ids = self.ids
        logging.info("Confirm Sheet Run Payslip %s "%(ids,))

        # Escribe fecha
        threaded_calculation = threading.Thread(target=self._confirm_sheet_run_date, args=(), name=ids)
        threaded_calculation.start()
        threaded_calculation.join()

        # Confirma la nomina
        threaded_calculation = threading.Thread(target=self._confirm_sheet_run_calculation, args=(), name=ids)
        threaded_calculation.start()
        threaded_calculation.join()


        # Escribe Mensajes
        threaded_calculation = threading.Thread(target=self._confirm_sheet_run_message, args=(), name=ids)
        threaded_calculation.start()
        threaded_calculation.join()

        """
        msg = ''
        Payslip = self.env['hr.payslip.run']
        for run in Payslip.browse(ids):
            for slip_id in run.slip_ids:
                if slip_id.mensaje_validar:
                    msg += "<b>Error Nomina %s</b><br />"%(slip_id.number)
                    msg += "<ol>%s</ol><br/>"%(slip_id.mensaje_validar)
                elif slip_id.mensaje_timbrado_pac:
                    msg += "<b>Mensaje TIMBRAR PAC %s</b><br />"%(slip_id.number)
                    msg += "<ul>%s</ul>"%(slip_id.mensaje_timbrado_pac)
                elif slip_id.mensaje_pac:
                    msg += "<b>Mensaje CANCELAR PAC %s</b><br />"%(slip_id.number)
                    msg += "<ul>%s</ul>"%(slip_id.mensaje_validar)
            if len(msg) != 0:
                run.message_post(body=msg)
        """
        return {}

    @api.multi
    def refund_sheet_run(self):
        for run in self:
            for slip_id in run.slip_ids:
                if slip_id.state in ['confirm', 'done']:
                    slip_id.action_payslip_cancel_nomina()

    @api.multi
    def compute_sheet_run_line(self):
        for sheet_run in self:
            amount_total = 0.0
            for payslip in sheet_run.slip_ids:
                amount_total += payslip.total
            sheet_run.write({'total': amount_total})
        return {}

    @api.multi
    def write(self, values):
        if 'fecha_pago' in values:
            r = self.slip_ids.write({'fecha_pago': self.fecha_pago})
        if 'concepto' in values:
            r = self.slip_ids.write({'concepto': self.concepto})
        result = super(HrPayslipRun, self).write(values)
        return result


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"
       
    @api.one
    @api.depends('total', 'salary_rule_id', 'gravado', 'exento')
    def _get_gravado(self):
        tipo = self.salary_rule_id and self.salary_rule_id.gravado_o_exento or 'gravado'
        self.gravado = self.total if tipo == 'gravado' else 0.0
        self.exento = self.total if tipo == 'exento' else 0.0

    currency_id = fields.Many2one(related='slip_id.currency_id', string="Currency")
    gravado = fields.Monetary(string="Total Gravado", compute='_get_gravado', )
    exento = fields.Monetary(string="Total Exento", compute='_get_gravado', )
    
    date_from = fields.Date(related='slip_id.date_from', string="De")
    date_to = fields.Date(related='slip_id.date_to', string="A")
    codigo_agrupador = fields.Char(related='salary_rule_id.codigo_agrupador_id.name', string="Código Agrupador")


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ['mail.thread', 'hr.payslip', 'account.cfdi']

    @api.model
    def _default_currency(self):
        currency_id = self.env.user.company_id.currency_id
        return currency_id

    @api.model
    def _default_fecha_pago(self):
        ctx = self._context
        fecha_pago = None
        if 'active_model' in ctx:
            run_id = self.env[ctx['active_model']].browse(ctx['active_id'])
            fecha_pago = run_id.fecha_pago
        return fecha_pago

    @api.one
    @api.depends('line_ids', 'line_ids.code')
    def _compute_total_payslip(self):
        line_total = 0.0
        if not self.line_ids:
            self.total = 0.0
        else:
            for line in self.line_ids:
                if 'total' in str(line.code).lower():
                    self.total = line.total
                    break
        return True

    currency_id = fields.Many2one('res.currency', string='Currency',
            required=True, readonly=True, 
            default=_default_currency, track_visibility='always')
    tipo_nomina = fields.Selection(selection=CATALOGO_TIPONOMINA, string=u"Tipo Nómina", required=True, default='O')
    fecha_pago = fields.Date(string="Fecha pago", required=True, default=_default_fecha_pago)
    retenido = fields.Monetary(string="ISR Retenido", copy=False)
    descuento = fields.Monetary(string="Total Deducciones sin ISR (Descuento)", copy=False)
    subtotal = fields.Monetary(string="Total Percepciones (Subtotal)", copy=False)
    concepto = fields.Char(string="Concepto", copy=False)
    total = fields.Monetary(string="Total Amount", copy=False, store=True, compute='_compute_total_payslip')
    source_sncf = fields.Selection([
            ('IP', 'Ingresos propios'),
            ('IF', 'Ingreso federales'),
            ('IM', 'Ingresos mixtos')],
        string="Recurso Entidad SNCF")
    amount_sncf = fields.Monetary(string="Monto Recurso SNCF")
    date_invoice = fields.Datetime(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False)
    monto_cfdi = fields.Monetary(string="Monto CFDI", copy=False)

    # Quitar en Futuras versiones
    fecha_local = fields.Datetime("Fecha y hora local", copy=False)
    cadena_original = fields.Text(string="Cadena Original", copy=False)
    certificado = fields.Char(string="No. Certificado", copy=False)
    fecha_sat = fields.Char(string="Fecha de Timbrado", copy=False)
    
    @api.multi
    def _calculation_confirm_sheet(self, ids, use_new_cursor=False):
        message = ''
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        payslip_id = self.env['hr.payslip'].browse(ids)
        payslip_id.action_payslip_done()
        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}


    # Para ser usado por el modulo de contabilidad electronica
    @api.multi
    def create_move_comprobantes(self):
        Move_Line = self.env['account.move.line']
        Comp = self.env['contabilidad_electronica.comprobante']

        N = len(self.ids)
        for indx, rec in enumerate(self):
            logging.info("Nomina %s - %s "%( indx+1, N ) )
            if rec.move_id and rec.uuid:
                uuid = rec.uuid
                for move_line in rec.move_id.line_ids:
                    res = Comp.search(['&',('uuid','=',uuid),('move_line_id','=',move_line.id)])
                    if len(res) > 0:
                        continue
                    comprobante = [(0,0,{
                        'monto': rec.monto_cfdi,
                        'uuid': uuid,
                        'rfc': rec.employee_id.rfc or (rec.address_home_id and rec.address_home_id.vat),
                    })]
                    Move_Line.browse([move_line.id]).write({'comprobantes': comprobante})
        return True


    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        context = dict(self._context)
        res = super(HrPayslip, self).get_payslip_lines(contract_ids, payslip_id)
        if context and 'cfdi_nomina' in context:
            for line in res:
                rule_id = line["salary_rule_id"]
                line.update(context["cfdi_nomina"][rule_id])
        return res

    def _get_days(self, code):
        context = dict(self._context) or {}
        dias = 0
        horas = 0
        for line in self.worked_days_line_ids:
            if line.code == code:
                dias = line.number_of_days
                horas = line.number_of_hours
                break
        else:
            message = "<li>Error \n\nNo se encontro entrada de dias trabajados con codigo %s</li>"%code
            self.action_raise_message(message)
        return dias, horas

    def _get_input(self, line):
        regla = line.salary_rule_id
        codigo = ''
        cantidad = 0
        for input in regla.input_ids:
            codigo = input.code
            break
        for input in self.input_line_ids:
            if input.code == codigo:
                cantidad = input.amount
                break
        return cantidad

    @api.multi
    def _get_code(self, line):
        if not line.salary_rule_id.codigo_agrupador_id:
            message = "<li>Error \n\nNo tiene codigo SAT: %s</li>"%line.salary_rule_id.name
            self.action_raise_message(message)
        codigo = line.salary_rule_id.codigo_agrupador_id.code
        nombre = line.salary_rule_id.codigo_agrupador_id.name
        return codigo, nombre

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


    def action_validate_cfdi(self):
        rec = self
        message = ''
        empleado = rec.employee_id
        tipo_jornada_id = empleado.tipo_jornada_id.code if empleado.tipo_jornada_id else None
        if not rec.journal_id.id in rec.company_id.cfd_mx_journal_ids.ids:
            return ''
        if rec.uuid:
            return ''
        if not rec.journal_id.codigo_postal_id:
            message += '<li>No se definio Lugar de Exception (C.P.)</li>'
        if not rec.tipo_nomina:
            message += '<li>El Atributo "Tipo Nomina" es requerido</li>'
        if not rec.date_from:
            message += '<li>El Atributo "Fecha Inicial del Periodo" es requerido</li>'
        if not rec.date_to:
            message += '<li>El Atributo "Fecha Final del Periodo" es requerido</li>'
        if not "%d"%self._get_days("WORK100")[0]:
            message += '<li>El Atributo "Numero de Dias Pagados" es requerido</li>'
        if not (empleado.curp or False):
            message += '<li>El Atributo "Receptor: CURP" es requerido</li>'
        if not (rec.contract_id.type_id and rec.contract_id.type_id.code or False):
            message += '<li>El Atributo "Receptor: TipoContrato" es requerido</li>'
        if not (rec.contract_id.regimen_contratacion_id and rec.contract_id.regimen_contratacion_id.code or False):
            message += '<li>El Atributo "Receptor: TipoRegimen" es requerido</li>'
        if not empleado.cod_emp:
            message += '<li>El Atributo "Receptor: NumEmpleado" es requerido</li>'
        if not (rec.contract_id.periodicidad_pago_id and rec.contract_id.periodicidad_pago_id.code or False):
            message += '<li>El Atributo "Receptor: PeriodicidadPago" es requerido</li>'
        if not (empleado.address_home_id and empleado.address_home_id.state_id.code):
            message += '<li>El Atributo "Receptor: ClaveEntFed" es requerido</li>'
        if not (empleado.fecha_alta) and not (empleado.contract_id and empleado.contract_id.date_start):
            message += '<li>El Atributo "Receptor: FechaInicioRelLaboral" es requerido</li>'
        if not empleado.imss:
            message += '<li>El Atributo "Receptor: NumSeguridadSocial" es requerido</li>'
        if not ((empleado.job_id and empleado.job_id.riesgo_puesto_id and empleado.job_id.riesgo_puesto_id.code) or (rec.company_id.riesgo_puesto_id and rec.company_id.riesgo_puesto_id.code) or False):
            message += '<li>El Atributo "Receptor: RiesgoPuesto" es requerido</li>'
        if not (empleado.sueldo_imss):
            message += '<li>El Atributo "Receptor: SalarioDiarioIntegrado" es requerido</li>'
        if tipo_jornada_id not in ['02', '03', '01', '04', '05', '06', '07', '08', '99']:
            message += '<li>El Atributo "Receptor: TipoJornada" es requerido</li>'
        self.action_raise_message(message)
        return message


    @api.multi
    def action_payslip_done_nomina(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.details_by_salary_rule_category:
                amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()

    @api.multi
    def action_payslip_done(self):
        res = False
        for rec in self:
            is_cfdi = rec.employee_id and rec.employee_id.contract_id and rec.employee_id.contract_id.is_cfdi or False
            if rec.uuid and rec.state not in ['draft']:
                return True
            if rec.uuid:
                return True
            if is_cfdi == False:
                return True

            logging.info('Action 00 %s '%(rec.number) )
            message = self.action_validate_cfdi()
            try:
                self.compute_sheet()
            except ValueError, e:
                message = str(e)
            except Exception, e:
                message = str(e)
            if message:
                self.action_raise_message("Error al Generar el XML \n\n %s "%( message.upper() ))
                return False
            if rec.total < 0:
                self.action_raise_message("Error al Generar el XML \n\n No se puede timbrar nominas con importe negativos")
                return True

            self.action_write_date_invoice_cfdi(rec.date_invoice_cfdi, self.id)
            res = rec.action_create_cfdi()
            if res == True:
                rec.action_payslip_done_nomina()
                # self.action_raise_message("Nomina timbrada")
                rec.write({'state': 'done'})
        return res

    def action_write_date_invoice_cfdi(self, date_invoice_cfdi, inv_id):
        if not date_invoice_cfdi:
            tz = self.env.user.tz or "UTC"
            hora_factura_utc = datetime.now(timezone("UTC"))
            dtz = hora_factura_utc.astimezone(timezone(tz)).strftime("%Y-%m-%d %H:%M:%S")
            dtz = dtz.replace(" ", "T")
            slip_id = self.sudo().env['hr.payslip'].browse(inv_id)
            slip_id.write({'date_invoice_cfdi': dtz})
            self._cr.commit()
        return {}


    def action_create_cfdi(self):
        ctx = dict(self._context) or {}
        self.read()
        if not self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids:
            return True        
        message = ""
        ctx['type'] = 'nomina'
        try:
            res = self.with_context(**ctx).stamp(self)
            if res.get('message'):
                message = res['message']
            else:
                self.get_process_data(self, res.get('result'))
        except ValueError, e:
            message = str(e)
        except Exception, e:
            message = str(e)
        if message:
            self.action_raise_message("Error al Generar el XML \n\n %s "%( message.upper() ))
            return False
        return True


    @api.multi
    def send_mail(self):
        return True

    @api.multi
    def action_payslip_cancel_nomina(self):
        context = dict(self._context) or {}
        if not self.uuid:
            self.move_id.reverse_moves()
            self.write({
                'state': 'cancel',
                'mandada_cancelar': True, 
                'mensaje_pac': ""
            })
            return True
        if context.get('state') == 'draft':
            return True
        if self.journal_id.id not in self.company_id.cfd_mx_journal_ids.ids:
            return True
        message = ''        
        res = self.cancel(self)
        if res.get('message'):
            message = res['message']
            message = message.replace("(u'", "").replace("', '')", "")
            self.action_raise_message("Error al Generar el XML \n\n %s "%( message.upper() ))
            return False
        else:
            acuse = res["result"].get("Acuse")
            self.move_id.reverse_moves()
            self.write({
                'state': 'cancel',
                'mandada_cancelar': True, 
                'mensaje_pac': """
                <strong>Fecha: </strong> %s<br />
                <strong>Folios</strong>%s<br />
                <strong>XML Acuse</strong><pre lang="xml"><code>%s</code></pre>
                """%(res["result"].get("Fecha"), res["result"].get("Folios"), acuse)
            })

            attachment_obj = self.env['ir.attachment']
            fname = "cancelacion_cfd_%s.xml"%(self.number.replace('/', '') or "")
            attachment_values = {
                'name': fname,
                'datas': base64.b64encode(acuse),
                'datas_fname': fname,
                'description': 'Cancelar Comprobante Fiscal Digital',
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary'
            }
            attachment_obj.create(attachment_values)
        return True


    @api.one
    def get_cantLetra(self, amount):
        cantLetra = cant_letra(self.currency_id, amount) or ''
        return cantLetra