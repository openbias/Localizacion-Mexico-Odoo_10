# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models, _

# [('zenpar', 'Zenpar (EDICOM)'), ('tralix', 'Tralix'), ('finkok', 'Finkok')]

class ResBank(models.Model):
    _inherit = 'res.bank'

    description = fields.Char(string="Nombre o razon social")

class company(models.Model):
    _inherit = 'res.company'

    
    cfd_mx_host = fields.Char(string="URL Stamp", size=256)
    cfd_mx_port = fields.Char(string="Port Stamp", size=256)
    cfd_mx_db = fields.Char(string="DB Stamp", size=256)
    
    cfd_mx_cer = fields.Binary(string='Certificado', filters='*.cer,*.certificate,*.cert', required=False, default=None)
    cfd_mx_key = fields.Binary(string='Llave privada', filters='*.key', required=False, default=None)
    cfd_mx_key_password = fields.Char('Password llave', size=64, invisible=False, required=False, default="")
    
    cfd_mx_test_nomina = fields.Boolean(string=u'Timbrar en modo de prueba (nómina)')
    cfd_mx_test = fields.Boolean(string='Timbrar Prueba', default=True)
    cfd_mx_pac = fields.Selection([('finkok', 'Finkok')], string="PAC", default='')
    cfd_mx_version = fields.Selection([('3.3', 'CFDI 3.3')], string='Versión', required=True, default='3.3')
    cfd_mx_journal_ids = fields.Many2many("account.journal", string="Diarios")

    reason_cancel_invoice = fields.Boolean(string="Motivo de Cancelacion Factura")

    
    # Quitar en Futuras versiones
    cfd_mx_finkok_user = fields.Char(string="Finkok User", size=64)
    cfd_mx_finkok_key = fields.Char(string="Finkok Password", size=64)
    cfd_mx_finkok_host = fields.Char(string="Finkok URL Stamp", size=256)
    cfd_mx_finkok_host_cancel = fields.Char(string="Finkok URL Cancel", size=256)
    cfd_mx_finkok_host_test = fields.Char(string="Finkok URL Stamp Modo Pruebas", size=256)
    cfd_mx_finkok_host_cancel_test = fields.Char(string="Finkok URL Cancel Modo Pruebas", size=256)
    cfd_mx_tralix_key = fields.Char(string="Tralix Customer Key", size=64)
    cfd_mx_tralix_host = fields.Char(string="Tralix Host", size=256)
    cfd_mx_tralix_host_test = fields.Char(string="Tralix Host Modo Pruebas", size=256)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: