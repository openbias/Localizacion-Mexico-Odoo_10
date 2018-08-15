# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re


class HrCurriculum(models.Model):
    _name = 'hr.curriculum'
    _description = "Employee's Curriculum"
    _inherit = 'ir.needaction_mixin'

    name = fields.Char('Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    description = fields.Text('Description')
    partner_id = fields.Many2one('res.partner', 'Partner', help="Employer, School, University, Certification Authority")
    location = fields.Char('Location', help="Location")
    expire = fields.Boolean('Expire', help="Expire", default=True)


class HrAcademic(models.Model):
    _name = 'hr.academic'
    _inherit = 'hr.curriculum'

    diploma = fields.Char('Diploma', translate=True)
    study_field = fields.Char('Field of study', translate=True)
    activities = fields.Text('Activities and associations', translate=True)

class HrCertification(models.Model):
    _name = 'hr.certification'
    _inherit = 'hr.curriculum'

    certification = fields.Char('Certification Number', help='Certification Number')
    category = fields.Selection([
            ('curso', 'Curso'),
            ('certificacion', 'Certificacion'),
            ('diplomado', 'Diplomado'),
            ('maestria', 'Maestria'),
        ], string='Category', required=True, default='curso', help='Category')

class HrExperience(models.Model):
    _name = 'hr.experience'
    _inherit = 'hr.curriculum'

    category = fields.Selection([
        ('professional', 'Professional'),
        ('academic', 'Academic'),
        ('certification', 'Certification')],
        string='Category', required=True, default='professional', help='Category')


class HrEmployeeDepends(models.Model):
    _name = "hr.employee.depends"
    _description = "Employee Dependents"
    _order = "employee_id,sequence,id"

    name = fields.Text(string='Name', required=True)
    sequence = fields.Integer(default=10, help="Gives the sequence of this line when displaying the employee.")
    birthday = fields.Date(string='Date of Birth', index=True, copy=False)
    type = fields.Selection([
            ('husband','Husband'),
            ('wife','Wife'),
            ('son','Son'),
            ('daughter','Daughter'),
            ('other','Other'),
        ], index=True, change_default=True,
        default=lambda self: self._context.get('type', 'wife'),
        track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee Reference', ondelete='cascade', index=True)



class Employee(models.Model):
    _inherit = 'hr.employee'
    _name = 'hr.employee'
    _rec_name = "nombre_completo"

    @api.one
    @api.depends('birthday')
    def _compute_employee_age(self):
        if self.birthday:
            self.age = relativedelta(
                fields.Date.from_string(fields.Date.today()),
                fields.Date.from_string(self.birthday)).years
        else:
            self.age = 0

    @api.one
    @api.depends('job_id')
    def _compute_last_writedate_job_id(self):
        if self.job_id:
            self.last_writedate_job_id = fields.Datetime.now()

    @api.one
    @api.depends('sueldo_diario')
    def _compute_last_writedate_sueldo_diario(self):
        if self.sueldo_diario:
            self.last_writedate_sueldo_diario = fields.Datetime.now()



    @api.model
    def _default_currency(self):
        currency_id = self.env.user.company_id.currency_id
        return currency_id

    @api.one
    @api.depends('appat', 'apmat', 'name')
    def _nombre_completo(self):
        self.nombre_completo = '%s %s %s'%( self.name, (self.appat or ''), (self.apmat or '') )

    currency_id = fields.Many2one('res.currency', string='Currency',
            required=True, readonly=True, 
            default=_default_currency)

    nombre_completo = fields.Char(string="Nombre Completo", store=True, compute='_nombre_completo')
    appat = fields.Char(string="Apellido Paterno", size=64, required=True, default="")
    apmat = fields.Char(string="Apellido Materno", size=64, required=True, default="")
    cod_emp = fields.Char(string="Codigo de Empleado", index=True, default='')
    tarjeta_nomina = fields.Char(string="Numero de Tarjeta de Nomina", size=64, default="")
    state_id = fields.Many2one('res.country.state', 'Place of Birth (State)')

    fecha_alta = fields.Date(string="Fecha Alta")
    fecha_baja = fields.Date(string="Fecha Baja")

    curp = fields.Char(string="CURP", size=18, default="")
    rfc = fields.Char(string="RFC", size=13, default="")
    
    sar = fields.Char(string="SAR", size=64, default="")

    imss = fields.Char(string="No. IMSS", size=64, default="")
    sueldo_imss = fields.Monetary(string='Sueldo Integrado al IMSS')
    retencion_imss_fija = fields.Monetary(string='Retencion IMSS Fija')
    imss_umf = fields.Char(string="Unidad de Medicina Familiar", default="")

    infonavit = fields.Char(string="No. Infonavit", size=64, default="")
    sueldo_infonavit = fields.Monetary(string='Sueldo Integrado al Infonavit')
    
    valor_descuento_fonacot = fields.Monetary(string='Valor Descuento Fonacot')

    valor_descuento_infonavit = fields.Monetary(string='Valor Descuento Infonavit')
    fecha_alta_infonavit = fields.Date(string="Alta Infonavit")
    tipo_descuento_infonavit_id = fields.Many2one("hr_mx_ext.tipodescuento", string="Tipo de Descuento")
    sueldo_diario = fields.Monetary(string='Sueldo Diario', track_visibility='onchange')
    retiro_parcialidad = fields.Float(string="Retiro", help="Monto diario percibido por el trabajador por jubilación, pensión o retiro cuando el pago es en parcialidades")
    anhos_servicio = fields.Integer(u"Número años de servicio")

    ife_anverso = fields.Binary(string='Anverso', filters='*.png,*.jpg,*.jpeg', attachment=True)
    ife_reverso = fields.Binary(string='Reverso', filters='*.png,*.jpg,*.jpeg', attachment=True)
    ife_numero = fields.Char(string="Clave de Elector", size=64, default="")
    licencia_anverso = fields.Binary(string='Anverso', filters='*.png,*.jpg,*.jpeg', attachment=True)
    licencia_reverso = fields.Binary(string='Reverso', filters='*.png,*.jpg,*.jpeg', attachment=True)
    licencia_numero = fields.Char(string="Numero", size=64, default="")
    licencia_vigencia = fields.Date(string="Vigencia")

    sindicalizado = fields.Boolean(string="Sindicalizado")
    tipo_jornada_id = fields.Many2one("hr_mx_ext.tipojornada", string="Tipo de Jornada")
    escolaridad_id = fields.Many2one("hr_mx_ext.escolaridad", string="Escolaridad")
    registro_patronal_id = fields.Many2one("hr_mx_ext.regpat", string="Registro Patronal")
    tipo_sueldo_id = fields.Many2one("hr_mx_ext.tiposueldo", string="Tipo Sueldo")
    tipo_trabajador_id = fields.Many2one("hr_mx_ext.tipotrabajador", string="Tipo Trabajador")
    zona_salario_id = fields.Many2one("hr_mx_ext.zonasalario", string="Zona Salario")
    forma_pago_id = fields.Many2one("hr_mx_ext.formapago", string="Forma de Pago")

    horas_jornada = fields.Integer(string="Horas Jornada")

    med_actividad = fields.Text(string="Actividad dentro de la Empresa")
    med_antecedentes_1 = fields.Text(string="Antecedentes Heredo Familiares")
    med_antecedentes_2 = fields.Text(string="Antecedentes Personales no Patologicos")
    med_antecedentes_3 = fields.Text(string="Antecedentes Personales Patologicos")
    med_padecimiento = fields.Text(string="Padecimento Actual")
    med_exploracion = fields.Text(string="Exploracion Fisica")
    med_diagnostico = fields.Text(string="Diagnostico")
    med_apto = fields.Boolean("Apto para el Puesto")

    job_id = fields.Many2one('hr.job', string='Job Title', track_visibility='onchange')
    age = fields.Integer(string='Age', readonly=True, compute='_compute_employee_age')
    work_extension_phone = fields.Char(string='Extension Phone', help='Internal phone number.')
    marital = fields.Selection(selection_add=[('free_union', 'Free Union')])
    employee_dependent_ids = fields.One2many('hr.employee.depends', 'employee_id', string='Dependents', copy=False)
    certification_ids = fields.One2many('hr.certification', 'employee_id', 'Certifications', help="Certifications")
    academic_ids = fields.One2many('hr.academic', 'employee_id', 'Academic experiences', help="Academic experiences")
    experience_ids = fields.One2many('hr.experience', 'employee_id', 'Professional Experiences', help='Professional Experiences')

    last_writedate_job_id = fields.Datetime(string='Latest Change Job', readonly=False, compute="_compute_last_writedate_job_id")
    last_writedate_sueldo_diario = fields.Datetime(string='Latest Change Salary', readonly=False, compute="_compute_last_writedate_sueldo_diario")

    @api.constrains('rfc')
    def _check_rfc(self):
        for rec in self:
            if rec.address_home_id and rec.address_home_id.vat != rec.rfc:
                raise ValidationError('El RFC "%s" no coincide con el del partner %s'%(rec.rfc, rec.address_home_id.vat))
        return True

    _sql_constraints = [
        ('cod_emp_uniq', 'unique (cod_emp)', "Error! Ya hay un empleado con ese codigo."),
    ]

    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = self.address_id.phone
        self.mobile_phone = self.address_id.mobile
        self.work_location = self.address_id.name

    @api.onchange('user_id')
    def _onchange_user(self):
        if self.user_id:
            self.work_email = self.user_id.email
            self.work_extension_phone = self.user_id.extension_phone
            # self.name = self.user_id.name
            self.image = self.user_id.image



    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     # TDE FIXME: strange
    #     if self._context.get('search_default_categ_id'):
    #         args.append((('categ_id', 'child_of', self._context['search_default_categ_id'])))
    #     return super(ProductProduct, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            result.append((inv.id, "%s %s %s" % (inv.name, inv.appat or '', inv.apmat or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_emp_ids = self.search([('cod_emp', 'ilike', name)] + args, limit=limit)
            appat_ids = self.search([('appat', 'ilike', name)] + args, limit=limit)
            apmat_ids = self.search([('apmat', 'ilike', name)] + args, limit=limit)
            if cod_emp_ids: recs += cod_emp_ids
            if appat_ids: recs += appat_ids
            if apmat_ids: recs += apmat_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    cod_emp = fields.Char(related='employee_id.cod_emp', store=True,  string=u"Codigo empleado", readonly=True)

class HrContract(models.Model):
    _inherit = "hr.contract"

    total_days_worked = fields.Integer(string="Days Worked", compute='_compute_total_days_worked')

    def _compute_total_days_worked(self):
        for contract in self:            
            date_start = contract.date_start
            date_end = contract.date_end if contract.date_end else fields.Date.today()

            date_start = datetime.strptime(date_start, "%Y-%m-%d")
            date_end = datetime.strptime(date_end, "%Y-%m-%d")
            delta = date_end - date_start
            contract.total_days_worked = delta.days



