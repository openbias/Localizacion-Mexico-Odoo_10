# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class ResCompany(models.Model):
    _inherit = "res.company"
    
    curp = fields.Char(string="CURP", help="Llenar en caso de que el empleador sea una persona física")
    riesgo_puesto_id = fields.Many2one("cfdi_nomina.riesgo_puesto", string="Clase riesgo")
