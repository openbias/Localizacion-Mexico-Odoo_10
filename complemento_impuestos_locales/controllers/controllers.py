# -*- coding: utf-8 -*-
from odoo import http

# class ComplementoImpuestosLocales(http.Controller):
#     @http.route('/complemento_impuestos_locales/complemento_impuestos_locales/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/complemento_impuestos_locales/complemento_impuestos_locales/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('complemento_impuestos_locales.listing', {
#             'root': '/complemento_impuestos_locales/complemento_impuestos_locales',
#             'objects': http.request.env['complemento_impuestos_locales.complemento_impuestos_locales'].search([]),
#         })

#     @http.route('/complemento_impuestos_locales/complemento_impuestos_locales/objects/<model("complemento_impuestos_locales.complemento_impuestos_locales"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('complemento_impuestos_locales.object', {
#             'object': obj
#         })