# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    fiscal_id = fields.Char(string='Fiscal ID', size=32, help="Tax identifier for Foreign partners.")
    supplier_type = fields.Selection([
        ('04','Proveedor Nacional'),
        ('05','Proveedor Extranjero'),
        ('15','Proveedor Global')], 
        string='Supplier Type', default='04', 
        help="Define the type of supplier, this field is used to get the DIOT report.")
    operation_type = fields.Selection([
        ('03','Prestación de Servicios Profesionales'),
        ('06','Arrendamiento de Inmuebles'),
        ('85','Otros')], 
        string='Operation Type', default='85', 
        help="Define the operation type, when partner type is 05 the only valid selections are 03 and 85, this field is used to get the DIOT report.")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
