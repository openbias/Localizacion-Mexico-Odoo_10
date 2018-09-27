# -*- coding: utf-8 -*-

import odoo
from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    journal_factoring_id = fields.Many2one('account.journal', string="Journal factoring")


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.one
    @api.depends('company_id')
    def _get_journal_factoring_id(self):
        self.journal_factoring_id = self.company_id.journal_factoring_id

    @api.one
    def _set_journal_factoring_id(self):
        if self.journal_factoring_id != self.company_id.journal_factoring_id:
            self.company_id.journal_factoring_id = self.journal_factoring_id

    journal_factoring_id = fields.Many2one('account.journal', compute='_get_journal_factoring_id', inverse='_set_journal_factoring_id', required=False,
        string='Journal factoring', help="Main journal of factoring.")