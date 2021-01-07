# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, _

from suds.client import Client
import time
from pytz import timezone
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)

# https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653,SF46410/datos/2019-11-01/2019-11-21?token=2e02dc5320d8b632c3a506954ccfc5fad9d325752eac0140a7cac213d2b637c7

def rate_retrieve_cop():
    WSDL_URL = 'https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService?WSDL'
    date = time.strftime('%Y-%m-%d')
    try:
        client = Client(WSDL_URL, location=WSDL_URL, faults=True)
        soapresp =  client.service.queryTCRM(date)
        if soapresp["success"] and soapresp["value"]:
            return {
                'COP': [{
                    'fecha': date,
                    'importe': soapresp["value"]
                }]
            }
        return False
    except Exception as e:
        _logger.info("---Error %s "%(str(e)))
        return False
    return False

class CurrencyRate(models.Model):
    _inherit = 'res.currency.rate'
    _name = 'res.currency.rate'

    rate = fields.Float(digits=(12, 10), help='The rate of the currency to the currency of rate 1')
    rate_inv = fields.Float(digits=(12, 10), help='The rate of the currency to the currency of rate 1')

class CurrencyRate(models.Model):
    _inherit = 'res.currency'
    _name = 'res.currency'

    @api.multi
    def _compute_current_rate(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name::DATE <= %s::DATE
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        for currency in self:
            currency.rate = currency_rates.get(currency.id) or 1.0

    @api.multi
    def _compute_current_rate_inv(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate_inv FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name::DATE <= %s::DATE
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        for currency in self:
            currency.rate = currency_rates.get(currency.id) or 1.0


    rate_inv = fields.Float(compute='_compute_current_rate_inv', string='Current Rate Inv', digits=(12, 10),
                        help='The rate of the currency to the currency of rate 1.')
    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 10),
                        help='The rate of the currency to the currency of rate 1.')


    # SF46407
    def getTipoCambio(self, fechaIni, fechaFin, token):
        url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653,SF46410,SF46407/datos"
        urlHost = '%s/%s/%s'%(url, fechaIni, fechaFin)
        response = requests.get(
            urlHost,
            params={'token': token},
            headers={'Accept': 'application/json', 'Bmx-Token': token, 'Accept-Encoding': 'gzip'},
        )
        json_response = response.json()
        tipoCambios = {}
        for bmx in json_response:
            series = json_response[bmx].get('series') or []
            for serie in series:
                idSerie = serie.get('idSerie') or ''
                if idSerie == 'SF60653':
                    idSerie = 'MXN'
                elif idSerie == 'SF46410':
                    idSerie = 'EUR'
                elif idSerie == 'SF46407':
                    idSerie = 'GBP'
                tipoCambios[idSerie] = []
                for dato in serie.get('datos', []):
                    fecha = datetime.strptime(dato.get('fecha'), '%d/%m/%Y').date()
                    importe = float(dato.get('dato'))
                    tipoCambios[idSerie].append({
                        'fecha': '%s'%fecha,
                        'importe': importe
                    })
        for tipoeur in tipoCambios.get('EUR', []):
            tipomxn = next(tipomxn for tipomxn in tipoCambios.get('MXN') if tipomxn["fecha"] == tipoeur['fecha'] )
            tipoeur['importe_real'] = tipoeur.get('importe')
            tipoeur['importe'] = tipomxn.get('importe', 0.0) / tipoeur.get('importe', 0.0)

        for tipogbp in tipoCambios.get('GBP', []):
            tipomxn = next(tipomxn for tipomxn in tipoCambios.get('MXN') if tipomxn["fecha"] == tipogbp['fecha'] )
            tipogbp['importe_real'] = tipogbp.get('importe')
            tipogbp['importe'] = tipomxn.get('importe', 0.0) / tipogbp.get('importe', 0.0)

        return tipoCambios

    @api.multi
    def refresh_currency(self, tipoCambios):
        Currency = self.env['res.currency']
        CurrencyRate = self.env['res.currency.rate']
        for moneda in tipoCambios:
            currency_id = Currency.search([('name', '=', moneda)])
            for tipo in tipoCambios[moneda]:
                if tipo['importe'] != 0.0:
                    rate_brw = CurrencyRate.search([('name', 'like', '%s 06:00:00'%tipo['fecha']), ('currency_id', '=', currency_id.id)])
                    vals = {
                        'name': '%s 06:00:00'%(tipo['fecha']),
                        'currency_id': currency_id.id,
                        'rate': tipo['importe'],
                        'company_id': False
                    }
                    if not rate_brw:
                        CurrencyRate.create(vals)
                        _logger.info('  ** Create currency %s -- date %s --rate %s ',currency_id.name, tipo['fecha'], tipo['importe'])
                    else:
                        CurrencyRate.write(vals)
                        _logger.info('  ** Update currency %s -- date %s --rate %s',currency_id.name, tipo['fecha'], tipo['importe'])
        return True

    @api.model
    def _run_currency_update(self):
        _logger.info(' === Starting the currency rate update cron')
        tz = self.env.user.tz
        date_cron = fields.Date.today()
        if tz:
            hora_factura_utc = datetime.now(timezone("UTC"))
            hora_factura_local = hora_factura_utc.astimezone(timezone(tz))
            date_end = hora_factura_local.date()
            date_start = date_end + relativedelta(days=-5)
        try:
            token = self.env['ir.config_parameter'].sudo().get_param('bmx.token', default='')
            if token:
                tipoCambios = self.getTipoCambio(date_start, date_end, token)
                self.refresh_currency(tipoCambios)
        except:
            pass
        try:
            tipoCambios = rate_retrieve_cop()
            self.refresh_currency(tipoCambios)
        except:
            pass

        return True

    def update_currency_rate_bias(self):
        self._run_currency_update()