# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields

class MyCustomReport(models.AbstractModel):
    _name = "my.custom.report"
    _description = "My Awesome custom report"

    @api.model
    def get_title(self):
        return _('Awesome report')

    @api.model
    def get_name(self):
        return _('awesome_custom_report')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


    @api.model
    def get_report_type(self):
        return self.env.ref('account_report_type')

    @api.model
    def get_lines(self, context_id, line_id=None):
        return []


class account_context_custom(models.TransientModel):
    _name = "account.context.coa"
    _description = "A particular context for the chart of account"
    _inherit = "account.report.context.common"

class account_context_coa(models.TransientModel):
    _name = "custom.context.report"
    _description = "A particular context for the chart of account"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.env['my.custom.report']