# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    is_employee = fields.Boolean('Es empleado')
