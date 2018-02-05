# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _

from openerp.addons.bias_base_report.bias_utis.amount_to_text_es_MX import amount_to_text

def cant_letra(currency, amount):
    if currency.name == 'MXN':
        nombre = currency.nombre_largo or 'pesos'
        siglas = 'M.N.'
    else:
        nombre = currency.nombre_largo or ''
        siglas = currency.name
    return amount_to_text().amount_to_text_cheque(float(amount), nombre,
                                                  siglas).capitalize()

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
            cantLetra = cant_letra(order.currency_id, order.amount_total)
            order.update({
                'cantLetra': cantLetra
            })
    cantLetra = fields.Char(string='Cantidad en letra', readonly=True, compute='_get_cantLetra', size=256, track_visibility='always')