# -*- coding: utf-8 -*-
from odoo import http

# class ComplementoPagos(http.Controller):
#     @http.route('/complemento_pagos/complemento_pagos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/complemento_pagos/complemento_pagos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('complemento_pagos.listing', {
#             'root': '/complemento_pagos/complemento_pagos',
#             'objects': http.request.env['complemento_pagos.complemento_pagos'].search([]),
#         })

#     @http.route('/complemento_pagos/complemento_pagos/objects/<model("complemento_pagos.complemento_pagos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('complemento_pagos.object', {
#             'object': obj
#         })