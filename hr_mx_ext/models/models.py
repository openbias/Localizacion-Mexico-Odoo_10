# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    registro_patronal_id = fields.Many2one('hr_mx_ext.regpat', string='Registro patronal')

class ResCountryState(models.Model):
    _inherit = "res.country.state"

    siglas_entidad = fields.Char(string='Siglas')


class TipoPensionados(models.Model):
    _name = 'hr_mx_ext.tipopensionados'
    _description = "Tipo Pensionados"
    
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
    _description = "Tipo de Trabajador"
    
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
    _description = "Tipo de Sueldo"
    
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
    _description = "Tipo de Jornada"

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
    _description = "Zona de Salario"

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
    _description = "Forma de Pago"
    
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
    _description = "Tipo Registro Patronal"
    
    name = fields.Char(string="Name", size=64, required=True, default="")
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('hr_mx_ext.regpat'))

class HrEscolaridad(models.Model):
    _name = "hr_mx_ext.escolaridad"
    _description = "Escolaridad"

    name = fields.Char(string="Name", size=64, required=True, default="")
    code = fields.Char(string="Code", required=True, default="")
    description = fields.Char(string="Description", size=64, required=True, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

