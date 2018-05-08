# -*- coding: utf-8 -*-

from cStringIO import StringIO
from odoo import api, fields, models, _
from odoo.report.report_sxw import report_sxw
from odoo.api import Environment

import logging
_logger = logging.getLogger(__name__)


class ReportZip(report_sxw):

    def create(self, cr, uid, ids, data, context=None):
        self.env = Environment(cr, uid, context)
        report_obj = self.env['ir.actions.report.xml']
        report = report_obj.search([('report_name', '=', self.name[7:])])
        if report.ids:
            self.title = report.name
            if report.report_type == 'zip':
                data.update(context)
                return self.create_zip_report(ids, data, report)
        return super(ReportZip, self).create(cr, uid, ids, data, context)

    def create_zip_report(self, ids, data, report):
        self.parser_instance = self.parser(self.env.cr, self.env.uid, self.name2, self.env.context)
        objs = self.getObjects(self.env.cr, self.env.uid, ids, self.env.context)

        self.parser_instance.set_context(objs, data, ids, 'xlsx')
        res = self.generate_zip_report(data, objs)
        return res

    def generate_zip_report(self, data, objs):
        raise NotImplementedError()