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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(PeriodicidadPago, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(OrigenRecurso, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()



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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(RegimenContratacion, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(ClaseRiesgo, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(CodigoAgrupador, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()
    

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

    @api.model
    def name_search(self, TipoHoras, args=None, operator='ilike', limit=100):
        recs = super(TipoHoras, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoIncapacidad, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoDeduccion, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoJornada, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoOtroPago, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoPercepcion, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


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