# -*- coding: utf-8 -*-

import odoo
from odoo import models, fields, api, _


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposeMessage, self).onchange_template_id(template_id,
                composition_mode, model, res_id)

        if model=='account.payment':
            payment_id = self.env[model].browse( res_id )
            if payment_id and payment_id.cfdi_timbre_id:
                xml_id = self.env["ir.attachment"].search([('name', '=', '%s.xml'%payment_id.cfdi_timbre_id.name )])
                if xml_id:
                    res['value'].setdefault('attachment_ids', []).append(xml_id[0].id)

        return res