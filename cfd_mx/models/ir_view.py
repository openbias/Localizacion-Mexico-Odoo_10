# -*- coding: utf-8 -*-

from odoo import fields, models

class IrView(models.Model):
    _inherit = 'ir.ui.view'

    is_addenda = fields.Boolean(
        string='Is an addenda?',
        help='If True, the view is an addenda for the Mexican invoicing.',
        default=False)