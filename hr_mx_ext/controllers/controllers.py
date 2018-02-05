# -*- coding: utf-8 -*-
from odoo import http

# class HrMxExt(http.Controller):
#     @http.route('/hr_mx_ext/hr_mx_ext/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_mx_ext/hr_mx_ext/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_mx_ext.listing', {
#             'root': '/hr_mx_ext/hr_mx_ext',
#             'objects': http.request.env['hr_mx_ext.hr_mx_ext'].search([]),
#         })

#     @http.route('/hr_mx_ext/hr_mx_ext/objects/<model("hr_mx_ext.hr_mx_ext"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_mx_ext.object', {
#             'object': obj
#         })