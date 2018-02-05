# -*- coding: utf-8 -*-
from odoo import http

# class ContabilidadElectronica(http.Controller):
#     @http.route('/contabilidad_electronica/contabilidad_electronica/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contabilidad_electronica/contabilidad_electronica/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('contabilidad_electronica.listing', {
#             'root': '/contabilidad_electronica/contabilidad_electronica',
#             'objects': http.request.env['contabilidad_electronica.contabilidad_electronica'].search([]),
#         })

#     @http.route('/contabilidad_electronica/contabilidad_electronica/objects/<model("contabilidad_electronica.contabilidad_electronica"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contabilidad_electronica.object', {
#             'object': obj
#         })