# -*- coding: utf-8 -*-

from odoo import models, fields, api

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ContabilidadElectronicaNaturaleza(models.Model):
    _name = "contabilidad_electronica.naturaleza"
    _description = "Naturaleza cuenta (catalogo anexo 24)"

    name = fields.Char(string='Naturaleza', index=True, required=True)
    code = fields.Char(string=u'Código', required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(ContabilidadElectronicaNaturaleza, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class ContabilidadElectronicaMetodoPago(models.Model):
    _name = "contabilidad_electronica.metodo.pago"
    _description = "Metodo de pago (catalogo anexo 24)"

    name = fields.Char(string='Concepto', index=True, required=True)
    code = fields.Char(string='Clave', required=True)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(ContabilidadElectronicaMetodoPago, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class ContabilidadElectronicaCodigoAgrupador(models.Model):
    _name = "contabilidad_electronica.codigo.agrupador"
    _description = "Codigo agrupador (catalogo anexo 24)"

    @api.multi
    def _get_accounts_ids(self):
        acc_obj = self.env['account.account']
        for cod in self:
            acc_ids = acc_obj.search([('codigo_agrupador_id','=', cod.id)])
            account_ids = []
            account_count = 0
            if acc_ids:
                account_count = len(acc_ids.ids)
                account_ids = acc_ids.ids
            cod.update({
                'account_count': account_count,
                'account_ids': account_ids
            })

    # Fields
    name = fields.Char(string=u'Código', index=True, required=True)
    description = fields.Char(string=u'Descripción')
    nivel = fields.Integer(string='Nivel', default=10)
    account_count = fields.Integer(string='# of Accounts', compute='_get_accounts_ids', readonly=True)
    account_ids = fields.Many2many("account.account", string='Accounts', compute="_get_accounts_ids", readonly=True, copy=False)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            name = "[%s] %s"%(rec.name, rec.description)
            result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(ContabilidadElectronicaCodigoAgrupador, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('description', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    
    @api.multi
    def get_codigo_agrupador_balanza(self, account):
        context = dict(self._context)
        cuenta = {
            'inicial': 0.0,
            'final': 0.0,
            'debe': 0.0,
            'haber': 0.0
        }
        if context.get('balanza', False):
            # trialbalance
            date_from = datetime.strptime(context.get('date_from'), '%Y-%m-%d').date()
            date_to = datetime.strptime(context.get('date_to'), '%Y-%m-%d').date()
            trialbalance = self.env['report.account.report_trialbalance']
            used_context = {
                'lang': 'en_US', 
                'date_from': date_from,
                'journal_ids': False, 
                'state': 'all', 
                'strict_range': True,# account.user_type_id.include_initial_balance, 
                'date_to': date_to
            }
            display_account = 'all'
            account_res = trialbalance.with_context( **used_context )._get_accounts(account, display_account)
            if account_res:
                cuenta['final'] = account_res[0]['balance']
                cuenta['debe'] = account_res[0]['debit']
                cuenta['haber'] = account_res[0]['credit']

            date_to = date_from + relativedelta(days=-1)
            used_context = {
                'lang': 'en_US', 
                'date_from': False,
                'journal_ids': False, 
                'state': 'all', 
                'strict_range': True,# account.user_type_id.include_initial_balance, 
                'date_to': date_to
            }
            account_res = trialbalance.with_context( **used_context )._get_accounts(account, display_account)
            if account_res:
                cuenta['final'] = (account_res[0]['balance'] + cuenta['debe']) - cuenta['haber']
                cuenta['inicial'] = account_res[0]['balance']
        return cuenta

    @api.multi
    def get_codigo_agrupador(self):
        context = dict(self._context)
        cuentas = []
        acc_obj = self.env['contabilidad_electronica.codigo.agrupador']
        cod_srch = acc_obj.search([])
        cod_ids = [x for x in cod_srch if x.account_count > 0]
        for cod_brw in cod_ids:
            for account in cod_brw.with_context( **context ).mapped('account_ids'):
                signo = 1 
                if account.naturaleza_id and account.naturaleza_id.code == "A":
                    signo = -1
                cuenta = {
                    'id': account.id,
                    'nivel': (cod_brw.nivel + 1),
                    'naturaleza': account.naturaleza_id and account.naturaleza_id.code or False,
                    'descripcion': account.name,
                    'codigo': account.code,
                    'codigo_agrupador': cod_brw.name or False,
                    'inicial': (account.initial * signo) if account.initial != 0.0 else account.initial,
                    'final': (account.balance * signo) if account.balance != 0.0 else account.balance,
                    'debe': account.debit,
                    'haber': account.credit
                }
                # if context.get('balanza', False):
                #     cuenta_balanza = self.with_context(**context).get_codigo_agrupador_balanza(account)
                #     if cuenta_balanza:
                #         cuenta.update(cuenta_balanza)
                cuentas.append(cuenta)
        return cuentas


class ContabilidadElectronicaComprobante(models.Model):
    _name = 'contabilidad_electronica.comprobante'
    _description = "Nodo Comprobante Nacional (Anexo 24)"

    uuid = fields.Char("UUID CFDI", size=36, required=True)
    monto = fields.Float("Monto", required=True)
    rfc = fields.Char("RFC", size=13, required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio")
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)

class ContabilidadElectronicaComprobanteOtro(models.Model):
    _name = 'contabilidad_electronica.comprobante.otro'
    _description = "Nodo Comprobante Nacional CFD o CBB (Anexo 24)"
    
    serie = fields.Char("Serie")
    folio = fields.Char("Folio", required=True)
    rfc = fields.Char("RFC", size=13, required=True)
    monto = fields.Float("Monto", required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio")
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)

class ContabilidadElectronicaComprobanteExtranjero(models.Model):
    _name = 'contabilidad_electronica.comprobante.ext'
    _description = "Nodo Comprobante Extranjero (Anexo 24)"
    
    num = fields.Char(u"Número del comprobante", required=True)
    tax_id = fields.Char(u"Identificador contribuyente")
    monto = fields.Float("Monto",  digits=(12,6), required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio", digits=(12,6),)
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)
    

class ContabilidadElectronicaTransferencia(models.Model):
    _name = 'contabilidad_electronica.transferencia'
    _description = "Nodo transferencia bancaria (anexo 24)"
    
    cta_ori_id = fields.Many2one("res.partner.bank", string="Cuenta origen", required=True)
    monto = fields.Float("Monto",  digits=(12,6), required=True)
    cta_dest_id = fields.Many2one("res.partner.bank", string="Cuenta destino", required=True)
    fecha = fields.Date("Fecha", required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio",  digits=(12,6),)
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)

class ContabilidadElectronicaCheque(models.Model):
    _name = "contabilidad_electronica.cheque"
    _description = "Nodo cheque (anexo 24)"
    
    num = fields.Char(u"Número del cheque", required=True)
    cta_ori_id = fields.Many2one("res.partner.bank", string="Cuenta origen", required=True)
    fecha = fields.Date("Fecha", required=True)
    monto = fields.Float("Monto",  digits=(12,6), required=True)
    benef_id = fields.Many2one("res.partner", string="Beneficiario", required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio", digits=(12,6),)
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)


class ContabilidadElectronicaOtroMetodoPago(models.Model):
    _name = "contabilidad_electronica.otro.metodo.pago"
    _description = "Nodo otro metodo de pago (anexo 24)"
    _rec_name = "metodo_id"

    metodo_id = fields.Many2one("contabilidad_electronica.metodo.pago", string=u"Método de pago", required=True)
    monto = fields.Float("Monto",  digits=(12,6), required=True)
    fecha = fields.Date("Fecha", required=True)
    benef_id = fields.Many2one("res.partner", string="Beneficiario", required=True)
    moneda_id = fields.Many2one("res.currency", string="Moneda")
    tipo_cambio = fields.Float("Tipo de cambio", digits=(12,6))
    move_line_id = fields.Many2one("account.move.line", required=True, string=u"Transacción", ondelete="cascade")
    move_line_name = fields.Char(string=u"Transacción", related='move_line_id.name', store=True)


class ContabilidadElectronicaAcuseSAT(models.Model):
    _name = 'contabilidad_electronica.acuse.sat'
    _description = 'Acuse SAT'
    _order = "fiscalyear, period_id, documento_id  asc"

    @api.model
    def _get_fiscalyear(self):
        fiscalyear = datetime.datetime.now().year
        if self.date_today:
            date_today = self.date_today.split('-')
            fiscalyear = '%s'%(date_today[0])
        self.onchange_date_today()
        return '%s'%(fiscalyear)

    @api.model
    def _get_fiscalyear_month(self):
        fiscalyear = datetime.datetime.now().month
        if self.date_today:
            date_today = self.date_today.split('-')
            fiscalyear = int(date_today[1])
        self.onchange_date_today()
        return '%02d'%(fiscalyear)


    @api.onchange('date_today')
    def onchange_date_today(self):
        if self.date_today:
            date_object = datetime.datetime.strptime(self.date_today, '%Y-%m-%d')
            last_day = calendar.monthrange(date_object.year,date_object.month)[1]
            self.fiscalyear = '%s'%(date_object.year)
            self.period_id = '%02d'%(date_object.month)
            self.date_from = '%s-%s-01'%(date_object.year, self.period_id)
            self.date_to = '%s-%s-%s'%(date_object.year, self.period_id, last_day)

    @api.onchange('documento_id')
    def onchange_documento_id(self):
        self.tipo_solicitud = None
        self.num_orden = None
        self.num_tramite = None
        xml = None
        fname = None
        xlsx = None
        fname_xlsx = None

    name = fields.Char(string=u"Acuse")
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    date_today = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Periodo (Mes y Año)")
    date_from = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Date From")
    date_to = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Date To")
    fiscalyear = fields.Char(u"Periodo (Año)", default=_get_fiscalyear)
    period_id = fields.Selection([
                        ('01', 'January'), 
                        ('02', 'February'), 
                        ('03', 'March'), 
                        ('04', 'April'), 
                        ('05', 'May'), 
                        ('06', 'June'), 
                        ('07', 'July'), 
                        ('08', 'August'), 
                        ('09', 'September'), 
                        ('10', 'October'), 
                        ('11', 'November'), 
                        ('12', 'December')
                    ], string="Periodo (Mes)", default=_get_fiscalyear_month)
    documento_id = fields.Selection([
                        ('01', 'Catalogo de Cuentas'), 
                        ('02', 'Balanza de Comprobacion'), 
                        ('03', 'Polizas del Periodo'),
                        ('04', 'Auxiliar Folios'),
                        ('05', 'Auxiliar Cuentas'),
                    ], string="Tipo de Documento Digital", default="01")
    xml = fields.Binary("Archivo XML")
    fname = fields.Char("Filename")
    message_validation_xml = fields.Html("NOTAS")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: