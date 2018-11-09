# -*- coding: utf-8 -*-

import json, requests

import odoo
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


# [('zenpar', 'Zenpar (EDICOM)'), ('tralix', 'Tralix'), ('finkok', 'Finkok')]

class ResBank(models.Model):
    _inherit = 'res.bank'

    description = fields.Char(string="Nombre o razon social")
    vat = fields.Char(string="RFC")

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



    @api.multi
    def action_ws_finkok_sat(self, service='', cfdi_params={}):
        self.ensure_one()
        url = "%s/cfdi/%s/%s/%s"%(self.cfd_mx_host, service, self.cfd_mx_db, self.vat)
        headers = {'Content-Type': 'application/json'}
        data = {
            "params": {
                "test": self.cfd_mx_test,
                "pac": self.cfd_mx_pac,
                "version": self.cfd_mx_version,
                "cfdi": cfdi_params
            }
        }
        data_json = json.dumps(data)
        res = requests.post(url=url, data=data_json, headers=headers)
        res_datas = res.json()
        dict_error = {}
        if res_datas.get('error') and res_datas['error'].get('data') and res_datas['error']['data'].get('message'):
            dict_error['message'] = res_datas['error']['data']['message']
        if res_datas.get('result') and res_datas['result'].get('error') and res_datas['result']['error'].get('message'):
            dict_error['message'] = res_datas['result']['error']['message']
        if res_datas.get('error'):
            dict_error['message'] = res_datas['error']

        if dict_error.get('message'):
            message = dict_error['message']
            return {'error': message}
            # raise UserError(message)
        else:
            return res_datas.get('result')
        return {}




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: