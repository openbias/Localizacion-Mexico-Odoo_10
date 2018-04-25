# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _

from openerp.addons.bias_base_report.bias_utis.amount_to_text_es_MX import amount_to_text

def extraeDecimales(nNumero, max_digits=2):
    strDecimales = str( round(nNumero%1, 2) ).replace('0.','')
    strDecimales += "0"*max_digits
    strDecimales = strDecimales[0:max_digits]
    return long( strDecimales )

def cant_letra(currency, amount):
    if currency.name == 'COP':
        nombre = currency.nombre_largo or 'M/CTE'
        siglas = 'M/CTE'

        decimales = extraeDecimales(amount, 2)
        am = str(round(amount, 2)).split('.')
        n_entero = amount_to_text().amount_to_text_cheque(float(am[0]), nombre, "").replace("  ", "").replace("00/100", "")
        n_decimales = amount_to_text().amount_to_text_cheque(float(decimales), 'centavos', siglas).replace("00/100 ", "")
        name = "%s con %s "%(n_entero, n_decimales)
    else:
        nombre = currency.nombre_largo or ''
        siglas = currency.name
        name = amount_to_text().amount_to_text_cheque(float(amount), nombre, siglas).capitalize()
    return name

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends(
        'amount_untaxed', 
        'amount_tax', 'amount_total',
        'order_line.price_total')
    def _get_cantLetra(self):
        for order in self:
            cantLetra = cant_letra(order.currency_id, order.amount_total)
            order.update({
                'cantLetra': cantLetra
            })
    cantLetra = fields.Char(string='Cantidad en letra', readonly=True, compute='_get_cantLetra', size=256, track_visibility='always')

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends(
        'amount_untaxed', 
        'amount_tax', 'amount_total',
        'order_line.price_total')
    def _get_cantLetra(self):
        for order in self:
            cantLetra = cant_letra(order.currency_id, order.amount_total)
            order.update({
                'cantLetra': cantLetra
            })
    cantLetra = fields.Char(string='Cantidad en letra', readonly=True, compute='_get_cantLetra', size=256, track_visibility='always')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends(
        'amount_untaxed', 
        'amount_tax', 'amount_total',
        'invoice_line_ids.price_subtotal')
    def _get_cantLetra(self):
        for order in self:
            if order.currency_id.name == 'COP':
                cantLetra = cant_letra(order.currency_id,(order.amount_untaxed*1.19))
                order.update({
                        'cantLetra': cantLetra
                })
            else:
                cantLetra = cant_letra(order.currency_id,order.amount_total)
                order.update({
                        'cantLetra': cantLetra
                })
    
    cantLetra = fields.Char(string='Cantidad en letra', readonly=True, compute='_get_cantLetra', size=256, track_visibility='always')