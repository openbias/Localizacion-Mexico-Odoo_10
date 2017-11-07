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
from openerp.exceptions import UserError

import time
from datetime import datetime
import calendar
from types import NoneType, StringType
import unicodedata
import base64
#import csv


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def remove_accents(s):
    def remove_accent1(c):
        return unicodedata.normalize('NFD', c)[0]
    return u''.join(map(remove_accent1, s))

QUERY_DIOT = """
SELECT
--  >>>>>>>>>     INFORMACION DE IDENTIFICACION DEL TERCERO DECLARADO     <<<<<<<<<<

--1 Tipo de tercero, Longitud: 2
  p.supplier_type::varchar(2),
--2 Tipo de operacion, Longitud: 2
  p.operation_type::varchar(2),
--3 Registro Federal de Contribuyentes, Longitud: 13
  TRANSLATE(p.vat, '-. ', '')::varchar(13) AS vat,
--4 Numero de ID fiscal, Longitud: 40
  MAX(CASE WHEN p.supplier_type='05' THEN p.fiscal_id END)::varchar(40) AS fiscal_id,
--5 Nombre del extranjero, Longitud: 43
  MAX(CASE WHEN p.supplier_type='05' THEN p.name END)::varchar(43) AS ext_name,
--6 Pais de residencia, Longitud: 2
  MAX(c.code)::varchar(2) AS country_code,
--7 Nacionalidad, Longitud: 40
  MAX(c.name)::varchar(40) AS country_name,

--  >>>>>>>>>     INFORMACION DE IMPUESTO AL VALOR AGREGADO (IVA)     <<<<<<<<<<
/*
tax_0   VAT 0
tax_1   VAT Exempt
tax_2   VAT Exempt Importation
tax_3   VAT 16
tax_4   VAT 16 Importation
tax_5   VAT 16 Not Creditable
tax_6   Retention VAT 4
tax_7   Retention VAT 10
tax_8   Retention VAT 10.67
tax_9   Retention ISR 10
tax_a   IEPS
tax_b   IEPS Importation
tax_c   
tax_d   
tax_e   
tax_f   
*/
--8 Valor de los actos o actividades pagados de IVA, Longitud: 12 
  NULLIF(TRUNC(COALESCE(SUM(f.base_0),0) + COALESCE(SUM(f.base_4),0)),0)::varchar(12) AS base_0_4,
--9 Valor de los actos o actividades pagados en la importacion de bienes y servicios de IVA, Longitud: 12 
  NULLIF(TRUNC(SUM(f.base_4)),0)::varchar(12) AS base_4_imp,
--10 Monto del IVA pagado no acreditable incluyendo importacion (correspondiente en la proporcion de las deducciones autorizadas), Longitud: 12
  NULLIF(TRUNC(SUM(f.tax_5)),0)::varchar(12) AS tax_5,
--11 Valor de los actos o actividades pagados en la importacion de bienes y servicios por los que no se pagara el IVA (Exentos), Longitud: 12
  NULLIF(TRUNC(SUM(f.base_2)),0)::varchar(12) AS base_2,
--12 Valor de los demas actos o actividades pagados a la tasa del 0% de IVA, Longitud: 12 
  NULLIF(TRUNC(SUM(f.base_0)),0)::varchar(12) AS base_0,
--13 Valor de los actos o actividades pagados por los que no se pagara el IVA (exentos), Longitud: 12 
  NULLIF(TRUNC(SUM(f.base_1)),0)::varchar(12) AS base_1,
--14 IVA Trasladado al contribuyente excepto importaciones de bienes y servicios (pagado), Longitud: 12 
  NULLIF(TRUNC(SUM(f.tax_3)),0)::varchar(12) AS tax_3,
--15 IVA pagado en las importaciones de bienes y servicios, Longitud: 12 
  NULLIF(TRUNC(SUM(f.tax_4)),0)::varchar(12) AS tax_4,
--16 IVA correspondiente a las devoluciones, descuentos y bonificaciones sobre compras, Longitud: 12
  NULL::varchar(12) AS returns
  
FROM
  account_move_fiscal f LEFT JOIN
  account_move m ON f.move_id = m.id LEFT JOIN
  res_partner p ON f.partner_id = p.id LEFT JOIN
  res_country c ON p.country_id = c.id 
"""

QUERY_WHERE = """
WHERE 
    m.company_id = %s AND
    f.operation_type = 'outcome' AND
    m.date >= '%s' AND m.date <= '%s' 
"""

QUERY_GROUP = """
GROUP BY p.supplier_type, p.operation_type, p.vat, p.id ORDER BY p.vat
"""

class account_diot(models.TransientModel):
    _name = 'account.diot'
    _description = 'Account DIOT'

    company_id = fields.Many2one('res.company', string='Company', readonly=False, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Date')
    date_to = fields.Date(string='End Date')
    diot_file = fields.Binary(string='DIOT File', readonly=True)
    filename = fields.Char(string='File Name')
    state = fields.Selection([('choose', 'choose'),('get', 'get')], default='choose')        

    ###########################################################################################################################################
    #       CREATE DIOT FILE
    ###########################################################################################################################################
    @api.multi
    def create_diot_file(self):
        self.date_from, self.date_to = self.get_month_day_range(self.date_from)
        query_where = QUERY_WHERE%(self.company_id.id, self.date_from, self.date_to)

        query = QUERY_DIOT + query_where + QUERY_GROUP # + 'LIMIT 1'
        self._cr.execute(query)
        diot_report_format = [desc[0] for desc in self._cr.description]
        result = self._cr.dictfetchall()
        if not result:
            raise UserError(_('Warning!\nThe report have no result'))
        csv_data = []
        # Order Correction
        for reg in result:
            row = []
            for key in diot_report_format:
                row.append(reg[key])
            csv_data.append(row)
            self.diot_file = self.ouput_csv(csv_data)
            self.filename ='DIOT_' + self.date_from[:-3] + '.txt'
            self.state = 'get'
        # Open DIOT Wizard
        module = 'account_tax_cash_basis_extended'
        action = 'action_account_diot'
        model, action_id = self.pool['ir.model.data'].get_object_reference(self._cr, self._uid, module, action)
        action = self.pool[model].read(self._cr, self._uid, action_id, context=self._context)
        action = self.pool[model].read(self._cr, self._uid, action_id)
        action.update({'res_id': self.id})
        return action

    @api.model
    def get_month_day_range(self, date):
        """
        For a date 'date' returns the start and end date for the month of 'date'.

        Month with 31 days:
        >>> date = datetime.date(2011, 7, 27)
        >>> get_month_day_range(date)
        (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

        Month with 28 days:
        >>> date = datetime.date(2011, 2, 15)
        >>> get_month_day_range(date)
        (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
        """
        d = datetime.strptime(date, '%Y-%m-%d')
        first_day = d.replace(day = 1)
        last_day = d.replace(day = calendar.monthrange(d.year, d.month)[1])
        return first_day, last_day

    @api.model
    def ouput_csv(self, csv_data):
        def process(d):
            if isinstance(d, unicode):
                d = remove_accents(d)
#                d = d.encode('utf-8')
            elif isinstance(d, (bool, NoneType)): 
                d = ''
            return d
        buf = StringIO()
        for datas in csv_data:
            row, first = '', False
            for d in datas:
                if isinstance(d, StringType):
                    row += (first and '|' or '') + process(d)
                else:
                    row += (first and '|' or '') + str(process(d))
                first = True
            buf.write(row+'\n')
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return out

account_diot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
