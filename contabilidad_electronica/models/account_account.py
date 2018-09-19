# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountAccount(models.Model):
    _inherit = 'account.account'

    codigo_agrupador_id = fields.Many2one('contabilidad_electronica.codigo.agrupador', 
                string="Codigo agrupador SAT", oldname="codigo_agrupador")
    naturaleza_id = fields.Many2one('contabilidad_electronica.naturaleza', 
                string="Naturaleza", oldname="naturaleza")

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.one
    def _get_tipo_poliza(self):
        tipo = '3'
        for move in self:
            if move.journal_id.type == 'bank':
                if move.journal_id.default_debit_account_id.id != move.journal_id.default_credit_account_id.id:
                    raise except_orm(_('Warning!'),
                        _('La cuenta deudora por defecto y la cuenta acreedora por defecto no son la misma en el diario %s'%move.journal_id.name ))
                if len(move.line_ids) == 2:
                    if move.line_ids[0].account_id.user_type_id.name in ['bank'] and move.line_ids[0].account_id.user_type_id.name in ['bank']:
                        tipo = '3'
                        break
                for line in move.line_ids:
                    if line.account_id.id == move.journal_id.default_debit_account_id.id:
                        if line.debit != 0 and line.credit == 0:
                            tipo = '1'
                            break
                        elif line.debit == 0 and line.credit != 0:
                            tipo = '2'
                            break
            else:
                tipo = '3'
        self.tipo_poliza = tipo
    

    tipo_poliza = fields.Selection([
            ('1','Ingresos'),
            ('2','Egresos'),
            ('3','Diario'),
        ], string="Tipo poliza", 
        compute='_get_tipo_poliza',
        default='3')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    comprobantes_ids = fields.One2many("contabilidad_electronica.comprobante", "move_line_id", 
        string="Comprobantes", ondelete="cascade", oldname="comprobantes")
    comprobantes_cfd_cbb_ids = fields.One2many("contabilidad_electronica.comprobante.otro", "move_line_id", 
        string="Comprobantes (CFD o CBB)", ondelete="cascade", oldname="comprobantes_cfd_cbb")
    comprobantes_ext_ids = fields.One2many("contabilidad_electronica.comprobante.ext", "move_line_id", 
        string="Comprobantes extranjeros", ondelete="cascade", oldname="comprobantes_ext")
    cheques_ids = fields.One2many("contabilidad_electronica.cheque", "move_line_id", 
        string="Cheques", ondelete="cascade", oldname="cheques")
    transferencias_ids = fields.One2many("contabilidad_electronica.transferencia", "move_line_id", 
        string="Transferencias", ondelete="cascade", oldname="transferencias")
    otros_metodos_ids = fields.One2many("contabilidad_electronica.otro.metodo.pago", "move_line_id", 
        string="Otros metodos de pago", ondelete="cascade", oldname="otros_metodos")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: