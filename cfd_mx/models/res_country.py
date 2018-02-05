# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, _


class banco(models.Model):
    _inherit = "res.bank"
    
    code_sat = fields.Char(u"Código SAT", required=True)
    razon_social = fields.Char(u"Razón social")
    extranjero = fields.Boolean("Banco extranjero")

class ResCountry(models.Model):
    _inherit = "res.country" 

    code_alpha3 = fields.Char(string="Codigo (alpha3)")

class CodigoPostal(models.Model):
    _name = "res.country.state.cp"

    name = fields.Char("Codigo Postal", size=128)
    state_id = fields.Many2one('res.country.state', string='Estado')
    ciudad_id = fields.Many2one('res.country.state.ciudad', string='Localidad')
    municipio_id = fields.Many2one('res.country.state.municipio', string='Municipio')

class Ciudad(models.Model):
    _name = 'res.country.state.ciudad'
    
    state_id = fields.Many2one('res.country.state', string='Estado', required=True)
    name = fields.Char(string='Name', size=256, required=True)
    clave_sat = fields.Char("Clave SAT")

class Municipio(models.Model):
    _name = 'res.country.state.municipio'
    
    name = fields.Char('Name', size=64, required=True)
    state_id = fields.Many2one('res.country.state', string='Estado', required=True)
    clave_sat = fields.Char("Clave SAT")

    # Quitar Futuras Versiones
    ciudad_id = fields.Many2one('res.country.state.ciudad', string='Ciudad')

class Colonia(models.Model):
    _name = 'res.country.state.municipio.colonia'
    
    codigo_postal_id = fields.Many2one('res.country.state.cp', string='Código Postal', required=True)
    municipio_id = fields.Many2one('res.country.state.municipio', string='Municipio', required=False)
    name = fields.Char(string='Name', size=256, required=True)
    clave_sat = fields.Char("Clave SAT")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: