# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    conta_elect_version = fields.Selection([
            ('1_1', 'Conta. Elect. 1.1'), 
            ('1_3', 'Conta. Elect. 1.3')],
        string='Conta. Elect. Version', required=True, default='1_3')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def create_move_comprobantes(self):
        comp_obj = self.env['contabilidad_electronica.comprobante']
        res = self.search([('state','!=','draft'), ('uuid', '!=', False), ('move_id', '!=', False)])
        for rec in res:
            rec.action_move_create_ce(rec.move_id.line_ids)
        return True

    @api.multi
    def action_move_create_ce(self, move_lines):
        comp_obj = self.env['contabilidad_electronica.comprobante']
        uuid = self.uuid or self.cfdi_timbre_id and self.cfdi_timbre_id.name or ''
        if self.uuid:
            if len(uuid) != 36:
                uuid = uuid[0:8]+'-'+uuid[8:12]+'-'+uuid[12:16]+'-'+uuid[16:20]+'-'+uuid[20:32]
                print self.number, self.id
            for move_line in move_lines:
                vals = {
                    'monto': self.amount_total,
                    'uuid': uuid,
                    'rfc': self.partner_id and self.partner_id.vat or '',
                    'move_line_id': move_line.id
                }
                if self.currency_id.name != "MXN":
                    vals.update({
                        'moneda_id': self.currency_id.id,
                        'tipo_cambio': self.tipo_cambio
                    })
                res = comp_obj.search([('move_line_id','=', move_line.id)])
                if len(res) > 0:
                    res.write(vals)
                else:
                    comp_obj.create(vals)
        return True

    @api.multi
    def invoice_validate(self):
        context = self._context
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            invoice.with_context(context).action_move_create_ce(invoice.move_id.line_ids)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: