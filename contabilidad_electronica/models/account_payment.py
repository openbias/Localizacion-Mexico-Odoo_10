# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountAbstractPayment(models.AbstractModel):
    _name = "account.abstract.payment"
    _inherit = "account.abstract.payment"

    cta_destino_id = fields.Many2one('res.partner.bank', string='Cuenta Destino', oldname="cta_destino")
    cta_origen_id = fields.Many2one('res.partner.bank', string='Cuenta Origen', oldname="cta_origen")
    cta_destino_partner_id = fields.Many2one('res.partner', string='Partner Cuenta Destino', oldname="cta_destino_partner")
    cta_origen_partner_id = fields.Many2one('res.partner', string='Partner Cuenta Origen', oldname="cta_origen_partner")
    fecha_trans = fields.Date(string='Fecha de la transferencia', default=fields.Date.context_today)
    num_cheque = fields.Char(string=u'Número')
    benef_id = fields.Many2one('res.partner', string='Beneficiario', oldname="benef")
    metodo_pago_id = fields.Many2one('contabilidad_electronica.metodo.pago', string=u'Código', oldname="metodo_pago")
    tipo_pago = fields.Selection([('trans', 'Transferencia'),('cheque', 'Cheque'), ('otro', 'Otro')], default='trans', string=u'Tipo del Pago')

    @api.onchange('journal_id')
    def _onchange_journal(self):
        rec = super(AccountAbstractPayment, self)._onchange_journal()
        self.cta_destino_id = None
        self.cta_origen_id = None
        if rec and self.partner_id and self.journal_id and self.partner_type:
            bank_ids = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            jb_ids = self.journal_id.bank_account_id
            if self.partner_type == "customer":
                self.cta_destino_id = jb_ids.ids
                rec['domain']['cta_destino_id'] = [('id', 'in', jb_ids.ids)]
                rec['domain']['cta_origen_id'] = [('id', 'in', bank_ids.ids)]
            else:
                self.cta_origen_id = jb_ids.ids
                rec['domain']['cta_origen_id'] = [('id', 'in', jb_ids.ids)]
                rec['domain']['cta_destino_id'] = [('id', 'in', bank_ids.ids)]
        return rec

class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"
    _description = "Register payments on multiple invoices"

    @api.model
    def default_get(self, fields):
        rec = super(AccountRegisterPayments, self).default_get(fields)
        if rec["payment_type"] == "inbound":
            rec["cta_origen_partner_id"] = rec.get('partner_id')
            rec["cta_destino_partner_id"] = self.env.user.company_id.id
        else:
            rec["cta_origen_partner_id"] = self.env.user.company_id.id
            rec["cta_destino_partner_id"] = rec.get('partner_id')
        return rec

    def get_payment_vals(self):
        """ Hook for extension """
        rec = super(AccountRegisterPayments, self).get_payment_vals()
        vals = {
            'cta_destino_id': self.cta_destino_id and self.cta_destino_id.id or None,
            'cta_origen_id': self.cta_origen_id and self.cta_origen_id.id or None,
            'cta_destino_partner_id': self.cta_destino_partner_id and self.cta_destino_partner_id.id or None,
            'cta_origen_partner_id': self.cta_origen_partner_id and self.cta_origen_partner_id.id or None,
            'fecha_trans': self.fecha_trans,
            'num_cheque': self.num_cheque,
            'benef_id': self.benef_id and self.benef_id.id or None,
            'metodo_pago_id': self.metodo_pago_id and self.metodo_pago_id.id or None,
            'tipo_pago': self.tipo_pago
        }
        rec.update(vals)
        return rec


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = "Payments"

    """
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            company_id = self.env.user.company_id
            self.cta_origen_partner_id = self.partner_id
            self.cta_destino_partner_id =  company_id.partner_id
            if self.partner_type == "customer":
                self.cta_origen_partner_id = self.partner_id
                self.cta_destino_partner_id = company_id.partner_id
            else:
                self.cta_origen_partner_id = company_id.partner_id
                self.cta_destino_partner_id = self.partner_id
            return {'domain': {}}
    """

    def _create_payment_entry_contabilidad_electronica(self, amount, move):
        obj = {
            'trans': self.env['contabilidad_electronica.transferencia'],
            'cheque': self.env['contabilidad_electronica.cheque'],
            'otro': self.env['contabilidad_electronica.otro.metodo.pago']
        }
        if self.tipo_pago:
            for m in move:
                for move_line in m.line_ids:
                    if self.tipo_pago == 'trans':
                        vals = {
                            'cta_ori_id': self.cta_origen_id.id,
                            'cta_dest_id': self.cta_destino_id.id,
                            'fecha': self.fecha_trans,
                        }
                    elif self.tipo_pago == 'cheque':
                        vals = {
                            'cta_ori_id': self.cta_origen_id.id,
                            'num': self.num_cheque,
                            'benef_id': self.benef_id.id,
                            'fecha': self.fecha_trans
                        }
                    else:
                        vals = {
                            'metodo_id': self.metodo_pago_id.id,
                            'benef_id': self.benef_id.id,
                            'fecha': self.fecha_trans
                        }
                    vals.update({
                        "move_line_id": move_line.id,
                        "monto": self.amount
                    })
                    if self.currency_id and self.currency_id.name != "MXN":
                        tipo_cambio = self._get_tipocambio(self.fecha_trans)
                        vals.update({
                            "moneda_id": self.currency_id.id,
                            "tipo_cambio":  tipo_cambio
                        })
                    obj[self.tipo_pago].create(vals)
        return True


    def _create_payment_entry(self, amount):
        move = super(AccountPayment, self)._create_payment_entry(amount)
        context = self._context
        self.with_context(context)._create_payment_entry_contabilidad_electronica(amount, move)
        return move

    def _get_tipocambio(self, date_invoice):
        model_obj = self.env['ir.model.data']
        tipocambio = 1.0
        if date_invoice:
            if self.currency_id.name=='MXN':
                tipocambio = 1.0
            else:
                tipocambio = model_obj.with_context(date=date_invoice).get_object('base', 'MXN').rate
        return tipocambio


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model
    def _default_benef(self):
        res = self.env.user.company_id.partner_id
        return res        

    @api.model
    def _default_metodo_pago(self):
        res = self.env['contabilidad_electronica.metodo.pago'].search([('code','=','01')], limit=1)
        return res

    cta_destino_id = fields.Many2one("res.partner.bank", string="Cuenta destino", oldname="cta_destino")
    cta_origen_id = fields.Many2one("res.partner.bank", string="Cuenta origen", oldname="cta_origen")
    num_cheque = fields.Char(string=u"Número")
    benef_id = fields.Many2one("res.partner", string="Beneficiario", default=_default_benef, oldname="benef")
    metodo_pago_id = fields.Many2one("contabilidad_electronica.metodo.pago", string=u"Código", default=_default_metodo_pago, oldname="metodo_pago")
    ttype = fields.Selection([
            ("trans", "Transferencia"),
            ("cheque", "Cheque"), 
            ("otro", "Otro")],
        'Type', required=True, default='otro')
    payment_type = fields.Selection([
            ('outbound', 'Send Money'), 
            ('inbound', 'Receive Money')], 
        string='Payment Type', required=True)

    @api.onchange('payment_type')
    def onchange_payment_type(self):
        rec = {}
        rec['domain'] = {
            'cta_origen_id': [],
            'cta_destino_id': []
        }
        self.cta_destino_id = None
        self.cta_origen_id = None
        if self.partner_id and self.journal_id and self.payment_type:
            bank_ids = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            jb_ids = self.journal_id.bank_account_id
            if self.payment_type == 'inbound':
                self.cta_destino_id = jb_ids.ids
                rec['domain']['cta_destino_id'] = [('id', 'in', jb_ids.ids)]
                rec['domain']['cta_origen_id'] = [('id', 'in', bank_ids.ids)]
            elif self.payment_type == 'outbound':
                self.cta_origen_id = jb_ids.ids
                rec['domain']['cta_origen_id'] = [('id', 'in', jb_ids.ids)]
                rec['domain']['cta_destino_id'] = [('id', 'in', bank_ids.ids)]

        return rec

    @api.onchange('ttype')
    def onchange_ttype(self):
        self.benef_id = None


    """
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = {}
        cta_ids = []
        cta_ids.append(self.env.user.company_id.partner_id.id)
        cta_ids.append(self.partner_id.id)
        res['domain'] = {
            'cta_origen_id': [('partner_id', 'in', cta_ids)],
            'cta_destino_id': [('partner_id', 'in', cta_ids)]
        }
        return res
    """


    def process_reconciliation_cont_elect(self, move_id, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        context = self._context

        cur_obj = self.env['res.currency']
        model_obj = self.env['ir.model.data']

        obj = {
            'trans': self.env['contabilidad_electronica.transferencia'],
            'cheque': self.env['contabilidad_electronica.cheque'],
            'otro': self.env['contabilidad_electronica.otro.metodo.pago']
        }

        st_line = move_id.statement_line_id
        currency_id = st_line.currency_id and st_line.currency_id or st_line.company_id.currency_id or None

        for move_line in move_id.line_ids:
            if st_line.ttype == 'trans':
                vals = {
                    'cta_ori_id': st_line.cta_origen_id.id,
                    'cta_dest_id': st_line.cta_destino_id.id,
                    'fecha': st_line.date,
                }
            elif st_line.ttype == 'cheque':
                vals = {
                    'cta_ori_id': st_line.cta_origen_id.id,
                    'num': st_line.num_cheque,
                    'benef_id': st_line.benef_id.id,
                    'fecha': st_line.date
                }
            else:
                vals = {
                    'metodo_id': st_line.metodo_pago_id.id,
                    'benef_id': st_line.benef_id.id,
                    'fecha': st_line.date
                }
            vals.update({
                "move_line_id": move_line.id,
                "monto": st_line.amount
            })
            if currency_id and self.currency_id.name != "MXN":
                tipo_cambio = self._get_tipocambio(st_line.date)
                vals.update({
                    "moneda_id": self.currency_id.id,
                    "tipo_cambio":  tipo_cambio
                })
            # if currency_id and currency_id.name != "MXN":
            #     mxn_currency_id = model_obj.get_object('base', 'MXN').id
            #     ctx = {'date': st_line.date}
            #     if cur_obj.read([currency_id], ["base"]):
            #         rate_other = 1.0
            #     else:
            #         rate_other = cur_obj.browse(currency_id)._get_current_rate('rate', [], context=ctx)[currency_id]
            #     rate_mxn = cur_obj.browse(mxn_currency_id)._get_current_rate('rate', [], context=ctx)[mxn_currency_id]
            #     tipo_cambio = (1.0 / rate_other) * rate_mxn
            #     vals.update({
            #         "moneda_id": currency_id.id,
            #         "tipo_cambio":  tipo_cambio
            #     })
            obj[st_line.ttype].create(vals)

    def _get_tipocambio(self, date_invoice):
        model_obj = self.env['ir.model.data']
        tipocambio = 1.0
        if date_invoice:
            if self.currency_id.name=='MXN':
                tipocambio = 1.0
            else:
                tipocambio = model_obj.with_context(date=date_invoice).get_object('base', 'MXN').rate
        return tipocambio


    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        res = super(account_bank_statement_line, self).process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        self.process_reconciliation_cont_elect(res, counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: