# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, _


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
    
    municipio_id = fields.Many2one('res.country.state.municipio', string='Municipio', required=True)
    name = fields.Char(string='Name', size=256, required=True)
    cp = fields.Char(string='Código Postal', size=10)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: