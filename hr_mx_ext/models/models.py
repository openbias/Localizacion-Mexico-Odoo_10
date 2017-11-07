# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    is_employee = fields.Boolean('Es empleado')

class ResCompany(models.Model):
    _inherit = "res.company"

    registro_patronal_id = fields.Many2one('hr_mx_ext.regpat', string='Registro patronal')

class ResCountryState(models.Model):
    _inherit = "res.country.state"

    siglas_entidad = fields.Char(string='Siglas')


class TipoPensionados(models.Model):
    _name = 'hr_mx_ext.tipopensionados'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoDescuento(models.Model):
    _name = 'hr_mx_ext.tipodescuento'
    _description = 'Tipo de descuento Infonavit (Tipo de Credito)'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoTrabajador(models.Model):
    _name = 'hr_mx_ext.tipotrabajador'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoSueldo(models.Model):
    _name = 'hr_mx_ext.tiposueldo'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoJornada(models.Model):
    _name = "hr_mx_ext.tipojornada"

    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class ZonaSalario(models.Model):
    _name = 'hr_mx_ext.zonasalario'

    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", default="")
    description = fields.Char(string="Description", size=64, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result
    
class FormaPago(models.Model):
    _name = 'hr_mx_ext.formapago'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")
    description = fields.Char(string="Description", size=64, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class RegistroPatronal(models.Model):
    _name = 'hr_mx_ext.regpat'
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('hr_mx_ext.regpat'))

class HrEscolaridad(models.Model):
    _name = "hr_mx_ext.escolaridad"

    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")
    description = fields.Char(string="Description", size=64, required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result



# class hr_mx_ext(models.Model):
#     _name = 'hr_mx_ext.hr_mx_ext'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100