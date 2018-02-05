# coding: utf-8
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re
from odoo import models, api, fields, _

class AccountAccountTemplate(models.Model):
    _inherit = 'account.account.template'

    codigo_agrupador = fields.Many2one('contabilidad_electronica.codigo.agrupador', 
                string=u"Código agrupador SAT")
    naturaleza = fields.Many2one('contabilidad_electronica.naturaleza', 
                string=u"Naturaleza")
    parent_id = fields.Many2one('account.account.template', 'Parent')
    type = fields.Selection([
            ('view', 'View'),
            ('other', 'Regular'),
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('liquidity', 'Liquidity'),
            ('consolidation', 'Consolidation'),
            ('closed', 'Closed'),
            ], 'Account Type', 
            )



