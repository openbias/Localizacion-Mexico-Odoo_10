# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    serie = fields.Char(string='Serie', size=32)
    codigo_postal_id = fields.Many2one('res.country.state.cp', string="C.P. Catálogo SAT", required=False)
    
    # Quitar Futuras Versiones
    lugar = fields.Char(string='Lugar de expedición', size=128)

class AccountTax(models.Model):
    _inherit = 'account.tax'

    cfdi_tipofactor = fields.Selection([
            ('Tasa', 'Tasa'),
            ('Cuota', 'Cuota'),
            ('Exento', 'Exento')],
        string="CFDI Tipo Factor", default='Tasa')

    # Quitar Futuras Versiones
    categoria = fields.Selection([
            ('iva', 'IVA'),
            ('ieps', 'IEPS'),
            ('iva_ret', 'Ret. IVA'),
            ('isr_ret', 'Ret. ISR'),
            ('tax_local','Traslados Locales'),
            ('retain_local','Retenciones Locales')],
        string="Categoria CFD")


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    cfdi_traslado = fields.Boolean(string="Traslado ?")
    cfdi_retencion = fields.Boolean(string="Retencion ?")
    cfdi_impuestos = fields.Selection([
            ('001', 'ISR'),
            ('002', 'IVA'),
            ('003', 'IEPS')],
        string=u"CFDI Catálogo de Impuestos", default='002')


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    nombre_largo = fields.Char(string="Nombre largo", size=256, 
        help="Ejemplo: dólares americanos, francos suizos")


