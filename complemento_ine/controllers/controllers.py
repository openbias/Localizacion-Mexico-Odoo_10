# -*- coding: utf-8 -*-
from odoo import http

# class ComplementoIne(http.Controller):
#     @http.route('/complemento_ine/complemento_ine/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/complemento_ine/complemento_ine/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('complemento_ine.listing', {
#             'root': '/complemento_ine/complemento_ine',
#             'objects': http.request.env['complemento_ine.complemento_ine'].search([]),
#         })

#     @http.route('/complemento_ine/complemento_ine/objects/<model("complemento_ine.complemento_ine"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('complemento_ine.object', {
#             'object': obj
#         })