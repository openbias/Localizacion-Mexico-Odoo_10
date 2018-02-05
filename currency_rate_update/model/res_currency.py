# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from openerp import models, fields, api, _
from openerp import exceptions
from ..services import update_service_MX_BdM
from datetime import date, datetime
from pytz import timezone

_logger = logging.getLogger(__name__)

import openerp
from openerp.osv import osv


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


    rate_inv = fields.Float(compute='_compute_current_rate_inv', string='Current Rate Inv', digits=(12, 8),
                        help='The rate of the currency to the currency of rate 1.')
    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 10),
                        help='The rate of the currency to the currency of rate 1.')
    
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
    def run_currency_update_bias(self):
        _logger.info(' === Starting the currency rate update cron')
        tz = self.env.user.tz
        date_cron = fields.Date.today()
        if tz:
            hora_factura_utc = datetime.now(timezone("UTC"))
            hora_factura_local = hora_factura_utc.astimezone(timezone(tz))
            date_cron = hora_factura_local.date()
        services = {
            'cron': True,
            'date_cron': date_cron
        }
        rate_dict = update_service_MX_BdM.rate_retrieve()
        rate_mxn = rate_dict.get('MXN', 0.0)
        ctx_mx = {
            'date_cron': date_cron,
            'rate': float(rate_mxn)
        }
        mxn = self.env.ref('base.MXN').with_context(**ctx_mx).refresh_currency()
        if rate_dict.get('EUR') and rate_dict.get('MXN'):
            rate_eur = rate_dict.get('EUR', 0.0)
            ctx_eur = {
                'date_cron': date_cron,
                'rate': float(rate_mxn) / float(rate_eur),
                'rate_inv': float(rate_mxn)

            }
            eur = self.env.ref('base.EUR').with_context(**ctx_eur).refresh_currency()

        # res = self.search([('name', '=', 'MXN')]).with_context(**services).refresh_currency()
        _logger.info(' === End of the currency rate update cron')
        return True

    @api.model
    def _run_currency_update(self):
        self.run_currency_update_bias()

    @api.multi
    def update_currency_rate_bias(self):
        self.run_currency_update_bias()