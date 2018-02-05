# -*- coding: utf-8 -*-

import odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

from datetime import date, datetime
from pytz import timezone
import json

class AccountAbstractPayment(models.AbstractModel):
    _name = "account.abstract.payment"
    _inherit = "account.abstract.payment"

    hide_formapago_id = fields.Boolean(compute='_compute_hide_formapago_id',
        help="Este campo es usado para ocultar el formapago_id, cuando no se trate de Recibo Electronico de Pago")
    formapago_id = fields.Many2one('cfd_mx.formapago', string=u'Forma de Pago')

    @api.one
    @api.depends('payment_type', 'journal_id')
    def _compute_hide_formapago_id(self):
        if not self.journal_id:
            self.hide_formapago_id = True
            return
        if self.journal_id.id in self.company_id.cfd_mx_journal_ids.ids:
            self.hide_formapago_id = False
        else:
            self.hide_formapago_id = True

class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = "account.payment"


    def action_validate_cfdi(self):
        ctx = dict(self._context) or {}
        user_id = self.env.user
        tz = user_id.tz or False

        message = ''
        if self.formapago_id:
            codigo_postal_id = self.journal_id and self.journal_id.codigo_postal_id or False
            regimen_id = self.company_id.partner_id.regimen_id or False
            if not codigo_postal_id:
                message += '<li>No se definio Lugar de Exception (C.P.)</li>'
            if not regimen_id: 
                message += '<li>No se definio Regimen Fiscal para la Empresa</li>'
            if not tz:
                message += '<li>El usuario no tiene definido Zona Horaria</li>'
            if not self.partner_id.vat:
                message += '<li>No se especifico el RFC para el Cliente</li>'
            if not self.company_id.partner_id.vat:
                message += '<li>No se especifico el RFC para la Empresa</li>'
            print 'message', message
        self.action_raise_message(message)
        return message


    @api.multi
    def post(self):
        for rec in self:
            rec.action_validate_cfdi()
        res = super(AccountPayment, self).post()
        return res