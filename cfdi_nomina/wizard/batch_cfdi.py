# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class batch_cfdi(models.TransientModel):
    _name = "cfdi_nomina.batch_cfdi"

    fecha_pago = fields.Date(string="Fecha pago", required=True)
    nomina_ids = fields.Many2many("hr.payslip", required=True, string=u"Nóminas")
    concepto = fields.Char(string="Concepto", required=True)
    metodo_pago_id = fields.Many2one("cfd_mx.formapago", string=u"Método de pago", required=True)
    
    @api.multi
    def action_batch_cfdi(self):
        context = dict(self._context)
        for this in self:
            context = context or {}
            context["fecha_pago"] = this.fecha_pago
            context["metodo_pago"] = this.metodo_pago_id.clave
            this.nomina_ids.write({'concepto': this.concepto})
            this.nomina_ids.with_context(**context).action_create_cfdi()
        return True


class batch_mail(models.TransientModel):
    _name = "cfdi_nomina.batch_mail"

    nomina_ids = fields.Many2many("hr.payslip", required=True, string=u"Nóminas")
    
    @api.multi
    def action_batch_mail(self):
        context = dict(self._context)
        for this in self:
            context = context or {}
            this.nomina_ids.with_context(**context).send_mail()
        return True