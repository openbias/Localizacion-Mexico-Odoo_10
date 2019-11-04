# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, _

from pytz import timezone
import requests
from datetime import datetime


_logger = logging.getLogger(__name__)





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


    def getTipoCambio(self, fechaIni, fechaFin, token):
        url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653,SF46410/datos"
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
                tipoCambios[idSerie] = []
                for dato in serie.get('datos', []):
                    fecha = datetime.strptime(dato.get('fecha'), '%d/%m/%Y').date()
                    importe = float(dato.get('dato'))
                    tipoCambios[idSerie].append({
                        'fecha': '%s'%fecha,
                        'importe': importe
                    })
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
            date_cron = hora_factura_local.date()

        try:
            token = self.env['ir.config_parameter'].sudo().get_param('bmx.token', default='')
            if token:
                tipoCambios = self.getTipoCambio(date_cron, date_cron, token)
                self.refresh_currency(tipoCambios)
        except:
            pass
        return True

    """
    @api.one
    def refresh_currency(self):
        context = dict(self._context)
        rate_obj = self.env['res.currency.rate']
        rate = context.get('rate', 0.0)
        rate_inv = context.get('rate_inv', 0.0)
        date_cron = '%s'%(context.get('date_cron'))
        rate_brw = rate_obj.search([('name', 'like', '%s 06:00:00'%(date_cron) ), ('currency_id', '=', self.id)])
        if rate != 0.0 :
            vals = {
                'name': '%s 06:00:00'%(date_cron),
                'currency_id': self.id,
                'rate': rate,
                'company_id': False
            }
            if rate_inv:
                vals['rate_inv'] = rate_inv
            if not rate_brw:
                rate_obj.create(vals)
                _logger.info('  ** Create currency %s -- date %s --rate %s ',self.name, date_cron, rate)
            else:
                rate_obj.write(vals)
                _logger.info('  ** Update currency %s -- date %s --rate %s',self.name, date_cron, rate)
        return True

    @api.multi
    def run_currency_update_bias_old(self):
        _logger.info(' === Starting the currency rate update cron')
        tz = self.env.user.tz
        date_cron = fields.Date.today()
        if tz:
            hora_factura_utc = datetime.now(timezone("UTC"))
            hora_factura_local = hora_factura_utc.astimezone(timezone(tz))
            date_cron = hora_factura_local.date()

        rate_dict = update_service_MX_BdM.rate_retrieve()
        for rate in rate_dict:
            ctx = {
                'date_cron': date_cron,
                'rate': rate_dict[rate]
            }
            self.env.ref('base.%s'%(rate)).with_context(**ctx).refresh_currency()
        _logger.info(' === End of the currency rate update cron')
        return True
    @api.multi
    def update_currency_rate_bias(self):
        self.run_currency_update_bias()
    @api.multi
    def get_currency_rate_today(self):
        self.ensure_one()
        rate_dict = update_service_MX_BdM.rate_retrieve()
        print 'rate_dict', rate_dict
        return rate_dict
    """

    def update_currency_rate_bias(self):
        self._run_currency_update()