# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

from urllib import urlopen
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', )

class CurrencyWizard(models.TransientModel):
    _name = "currency_rate_update_wizard"

    date_start = fields.Date(string="Fecha Inicial", required=True)
    date_stop = fields.Date(string="Fecha Final", required=True)



    def rate_retrieve_by_dates(self, dfecha, hfecha):
        rate_retrieve = {}
        url = "http://dof.gob.mx/indicadores_detalle.php?cod_tipo_indicador=158&dfecha=%s&hfecha=%s"%(dfecha, hfecha)
        try:
            html_data = urlopen(url).read()
            soup = BeautifulSoup( html_data, 'html.parser')
            for l in soup.findAll('tr', 'Celda 1'):
                fecha = rate = l.findAll('td')[0].renderContents()
                rate = l.findAll('td')[-1].renderContents()
                rate_retrieve[fecha] = {
                    'date': fecha,
                    'rate': rate
                }
        except:
            pass
        return rate_retrieve

    def getUltimoTipoCambio(self, date_start, rate_datas):
        rate = 0.0
        date_start = date_start + relativedelta( days=-1)
        date_start_str = date_start.strftime('%d-%m-%Y')
        count = 0
        if rate_datas.get(date_start_str, False):
            rate = rate_datas[date_start_str]['rate']
        while (rate == 0.0) and (count < 10):
            date_start = date_start + relativedelta( days=-1)
            date_start_str = date_start.strftime('%d-%m-%Y')
            if rate_datas.get(date_start_str, False):
                rate = rate_datas[date_start_str]['rate']
            count += 1
        return rate

    def action_process_rate(self, date_from, date_to):
        date_start = datetime.strptime(date_from, '%Y-%m-%d')
        date_stop = datetime.strptime(date_to, '%Y-%m-%d')
        date_start_initial = date_start + relativedelta(days=-20)
        rate_datas = self.rate_retrieve_by_dates(date_start_initial.strftime('%d/%m/%Y'), date_stop.strftime('%d/%m/%Y'))
        indx = 1
        rate_retrieve = []
        while date_stop >= date_start:
            rate = self.getUltimoTipoCambio(date_start, rate_datas)
            date_start_str = date_start.strftime('%Y-%m-%d')
            rate_retrieve.append({
                'date': date_start_str,
                'rate': rate
            })
            date_start = date_start + relativedelta(days=+1)
            indx += 1       
        return rate_retrieve

    @api.multi
    def action_update_rate(self):
        Currency = self.env['res.currency']
        Rate = self.env['res.currency.rate']
        for rec in self:
            rate_retrieve = self.action_process_rate(rec.date_start, rec.date_stop)
            logging.info(' == rate_retrieve == %s ', rate_retrieve)
            currency_ids = Currency.search([('name', 'in', ['MXN', 'MN'])])
            for currency in currency_ids: 
                for line in rate_retrieve:
                    rate_name = line['date']
                    rate_ids = Rate.search([('name', 'like', '%s 06:00:00'%(rate_name) ), ('currency_id', '=', currency.id)])
                    vals = {
                        'name': '%s 06:00:00'%(rate_name),
                        'currency_id': currency.id,
                        'rate': line['rate'],
                        'company_id': False
                    }
                    if not rate_ids:
                        Rate.create(vals)
                        logging.info('  ** Create currency %s -- date %s --rate %s ', currency.name, line['date'], line['rate'])
                    else:
                        rate_ids.write(vals)
                        logging.info('  ** Update currency %s -- date %s --rate %s', currency.name, line['date'], line['rate'])