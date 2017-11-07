# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PeriodicidadPago(models.Model):
    _name = "cfdi_nomina.periodicidad_pago"
    _description = "Periodicidad Pago"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result


class OrigenRecurso(models.Model):
    _name = "cfdi_nomina.origen_recurso"
    _description = "Origen recurso"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result


class RegimenContratacion(models.Model):
    _name = "cfdi_nomina.regimen_contratacion"
    _descripcion = "Regimen contratacion"
    
    name = fields.Char(string="Descripción", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class ClaseRiesgo(models.Model):
    _name = "cfdi_nomina.riesgo_puesto"
    
    name = fields.Char(string="Descripción", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoRegla(models.Model):
    _name = "cfdi_nomina.tipo"
    
    name = fields.Char(string="Tipo", required=True)


class CodigoAgrupador(models.Model):
    _name = "cfdi_nomina.codigo_agrupador"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)
    tipo_id = fields.Many2one("cfdi_nomina.tipo", string="Tipo", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result
    

class TipoHoras(models.Model):
    _name = "cfdi_nomina.tipo_horas"
    _description = "Tipo horas"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result


class TipoIncapacidad(models.Model):
    _name = "cfdi_nomina.tipo_incapacidad"
    _description = "Tipo incapacidad"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoDeduccion(models.Model):
    _name = "cfdi_nomina.tipo_deduccion"
    _description = "Tipo deduccion"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result


class TipoJornada(models.Model):
    _name = "cfdi_nomina.tipo_jornada"
    _description = "Tipo jornada"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoOtroPago(models.Model):
    _name = "cfdi_nomina.tipo_otro_pago"
    _description = "Tipo Otro Pago"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

class TipoPercepcion(models.Model):
    _name = "cfdi_nomina.tipo_percepcion"
    _description = "Tipo Percepcion"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string=u"Código Catálogo SAT", required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result


class TablaSubsidio(models.Model):
    _name = "cfdi_nomina.hr_tabla_subsidio"

    name = fields.Char(string=u"Año", required=True)
    limite_inferior = fields.Float(string=u"Límite inferior", required=True)
    limite_superior = fields.Float(string=u"Límite superior", required=True)
    subsidio = fields.Float(string="Subsidio", required=True)

class TablaIsr(models.Model):
    _name = "cfdi_nomina.hr_tabla_isr"
    
    name = fields.Char(string=u"Año", required=True)
    limite_inferior = fields.Float(string=u"Límite inferior", required=True)
    limite_superior = fields.Float(string=u"Límite superior", required=True)
    cuota_fija = fields.Float(string="Cuota fija", required=True)
    tasa = fields.Float(string="Tasa (%)", required=True)

    @api.multi
    def calcular_isr(self, ingreso, name):
        tabla_id = self.search([('name', '=', name)], order='limite_inferior asc')
        if not tabla_id:
            raise UserError("Error \n\nNo hay tabla de ISR definida para el año %s"%name)
        rows = self.browse(tabla_id)
        r = rows[0]
        for row in rows:
            if row.limite_superior < 0:
                row.limite_superior = float("inf")
            if row.limite_inferior <= ingreso <= row.limite_superior:
                break
            r = row
        base = ingreso - r.limite_inferior
        isr_sin_subsidio = base * (r.tasa / 100.0) + r.cuota_fija
        
        tabla_s_obj = self.env['cfdi_nomina.hr_tabla_subsidio']
        tabla_id = tabla_s_obj.search([('name', '=', name)], order='limite_inferior asc')
        if not tabla_id:
            raise UserError("Error \n\nNo hay tabla de subsidio al empleo definida para el año %s"%name)
        rows = tabla_s_obj.browse(tabla_id)
        r = rows[0]
        for row in rows:
            if row.limite_superior < 0:
                row.limite_superior = float("inf")
            if row.limite_inferior <= ingreso <= row.limite_superior:
                break
            r = row
        isr = isr_sin_subsidio - r.subsidio
        return ingreso - isr