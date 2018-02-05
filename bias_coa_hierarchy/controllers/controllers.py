# -*- coding: utf-8 -*-
from odoo import http

# class BiasCoaHierarchy(http.Controller):
#     @http.route('/bias_coa_hierarchy/bias_coa_hierarchy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bias_coa_hierarchy/bias_coa_hierarchy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bias_coa_hierarchy.listing', {
#             'root': '/bias_coa_hierarchy/bias_coa_hierarchy',
#             'objects': http.request.env['bias_coa_hierarchy.bias_coa_hierarchy'].search([]),
#         })

#     @http.route('/bias_coa_hierarchy/bias_coa_hierarchy/objects/<model("bias_coa_hierarchy.bias_coa_hierarchy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bias_coa_hierarchy.object', {
#             'object': obj
#         })