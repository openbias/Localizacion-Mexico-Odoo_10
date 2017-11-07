# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

import datetime, calendar

class GenerarXmls(models.TransientModel):
    _name = "contabilidad_electronica.wizard.generar.xmls"
    _description = "Generar XMLs Anexo 24"    

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

    # Fields 
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    date_today = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Periodo (Mes y Año)")
    date_from = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Date From")
    date_to = fields.Date(required=True, index=True, default=fields.Date.context_today, string="Date To")
    fiscalyear = fields.Char(u"Periodo (Año)")
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
            ('12', 'December')],
        string="Periodo (Mes)")
    documento_id = fields.Selection([
            ('01', 'Catalogo de Cuentas'), 
            ('02', 'Balanza de Comprobacion'), 
            ('03', 'Polizas del Periodo'),
            ('04', 'Auxiliar Folios'),
            ('05', 'Auxiliar Cuentas')],
        string="Tipo de Documento Digital", default="01")
    tipo_envio = fields.Selection([
            ('N', 'Normal'),
            ('C','Complementaria')],
        string=u"Tipo de Envío de la Balanza",
        required=True, default='N')                                 # Balanza
    fecha_mod_bal = fields.Date(u"Última Modificación")             # Balanza
    tipo_solicitud = fields.Selection([
            ('AF', 'Acto de Fiscalización'),
            ('FC', 'Fiscalización Compulsa'),
            ('DE', 'Devolución'),
            ('CO', 'Compensación')
        ], string=u"Tipo de Solicitud de la Póliza")                    # Poliza
    num_orden = fields.Char(u"Número de Orden")                     # Poliza
    num_tramite = fields.Char(u"Número de Trámite")                 # Poliza

    xml = fields.Binary("Archivo XML")
    fname = fields.Char("Filename")
    xlsx = fields.Binary("Archivo XLSX")
    fname_xlsx = fields.Char("Filename XLSX")
    message_validation_xml = fields.Html("Validar XML")

    @api.multi
    def view_contabilidad_electronica(self):
        url="/sc"
        return {
            'type': 'ir.actions.act_url',
            'url':url,
            'context': self._context,
        }

    @api.multi
    def validar_contabilidad_electronica(self):
        url="https://ceportalvalidacionprod.clouda.sat.gob.mx/"
        return {
            'type': 'ir.actions.act_url',
            'url':url,
        }


    # 1. XML CATALOGO DE CUENTAS
    @api.multi
    def action_xml_catalogo(self):
        self.ensure_one()
        context = dict(self._context)
        cod_agrupador = self.env['contabilidad_electronica.codigo.agrupador']
        company_id = self.env.user.company_id
        vce = company_id.conta_elect_version or '1_3'
        data = {
            'mes': self._get_fiscalyear_month(),
            'ano': self._get_fiscalyear(),
            'rfc': company_id.vat,
            'cuentas': [],
            'version': vce
        }
        data['cuentas'] = cod_agrupador.get_codigo_agrupador()
        data["cuentas"].sort(key=lambda x: x["codigo"])
        fname = '%s%s%sCT'%(self.company_id.partner_id.vat or '', data.get('ano'), data.get('mes') )
        ctx = {
            'xml_file': 'xml_catalogo.xml',
            'xml_xsd': 'CatalogoCuentas_%s.xsd'%(vce),
            'xml_xslt': 'CatalogoCuentas_%s.xslt'%(vce),
            'fname': fname+'.xml',
            'version': vce
        }
        datas={
            "data": data,
            "ctx": ctx
        }
        self.with_context(**ctx)._save_xml(data)
        return self.with_context(**ctx)._return_action()

    # 2. XML BALANZA
    @api.multi
    def action_xml_balanza(self):
        self.ensure_one()
        context = dict(self._context)
        cod_agrupador = self.env['contabilidad_electronica.codigo.agrupador']

        company_id = self.env.user.company_id
        vce = company_id.conta_elect_version or '1_3'

        date_object = datetime.datetime.strptime(self.date_today, '%Y-%m-%d')
        last_day = calendar.monthrange(date_object.year,date_object.month)[1]
        data = {
            'mes': self._get_fiscalyear_month(),
            'ano': self._get_fiscalyear(),
            'rfc': company_id.vat,
            'cuentas': [],
            'tipo_envio': self.tipo_envio,
            'fecha_mod_bal': self.fecha_mod_bal,
            'version': vce
        }
        fname = '%s%s%sB%s'%(company_id.partner_id.vat or '', data.get('ano'), data.get('mes'), data.get('tipo_envio') )
        ctx = {
            'date_from': '%s-%s-01'%(date_object.year, date_object.month),
            'date_to': '%s-%s-%s'%(date_object.year, date_object.month, last_day),
            'balanza': True,
            'version': vce,
            'xml_file': 'xml_balanza.xml',
            'xml_xsd': 'BalanzaComprobacion_%s.xsd'%(vce),
            'xml_xslt': 'BalanzaComprobacion_%s.xslt'%(vce),
            'fname': fname+'.xml'
        }
        data['cuentas'] = cod_agrupador.with_context(**ctx).get_codigo_agrupador()
        data["cuentas"].sort(key=lambda x: x["codigo"])
        datas={
            "data": data,
            "ctx": ctx
        }
        self.with_context(**ctx)._save_xml(data)
        return self.with_context(**ctx)._return_action()

    # 2. XML POLIZAS
    def get_polizas_lines(self):
        if not self.tipo_solicitud:
            raise UserError('Favor de indicar el tipo de solicitud')
        move_obj = self.env['account.move']
        move_ids = move_obj.search(['&', ('date','>=',self.date_from), ('date','<=',self.date_to), ('company_id', '=', self.company_id.id)])
        return move_ids

    @api.multi
    def action_xml_polizas(self):
        self.ensure_one()
        context = dict(self._context)

        company_id = self.env.user.company_id
        vce = company_id.conta_elect_version or '1_3'

        date_object = datetime.datetime.strptime(self.date_today, '%Y-%m-%d')
        last_day = calendar.monthrange(date_object.year,date_object.month)[1]
        data = {
            'mes': self._get_fiscalyear_month(),
            'ano': self._get_fiscalyear(),
            'rfc': self.env.user.company_id.vat,
            'tipo_solicitud': self.tipo_solicitud,
            'polizas': [],
            'version': vce
        }
        if self.num_orden: data['num_orden'] = self.num_orden
        if self.num_tramite: data['num_tramite'] = self.num_tramite
        for move in self.get_polizas_lines():
            if len(move.line_ids) == 0:
                continue

            poliza = {
                "num": "%s-%s"%(move.tipo_poliza, move.name),
                "fecha": move.date,
                "concepto": move.ref or move.name,
                "transacciones": []
            }
            for move_line in move.line_ids:
                transaccion = {
                    "num_cta": move_line.account_id.code,
                    "des_cta": move_line.account_id.name,
                    "concepto": move_line.name,
                    "debe": move_line.debit,
                    "haber": move_line.credit,
                    'cheques': [],
                    'transferencias': [],
                    'otros_metodos': [],
                    'comprobantes': [],
                    'comprobantes_cfd_cbb': [],
                    'comprobantes_ext': []
                }
                #-----------------------------------------------------------
                for cheque in move_line.cheques_ids:
                    vals = {
                        "num": cheque.num,
                        "banco": cheque.cta_ori.bank_id.code_sat,
                        "cta_ori": cheque.cta_ori.acc_number,
                        "fecha": cheque.fecha,
                        "monto": cheque.monto,
                        "benef": cheque.benef_id.name,
                        "rfc": cheque.benef_id.vat
                    }
                    if cheque.cta_ori.bank_id.extranjero:
                        vals["banco_ext"] = cheque.cta_ori.bank_id.name
                    if cheque.moneda:
                        vals.update({
                            "moneda": cheque.moneda.name,
                            "tip_camb": cheque.tipo_cambio
                        })
                    transaccion["cheques"].append(vals)
                #-----------------------------------------------------------
                for trans in move_line.transferencias_ids:
                    vals = {                        
                        "cta_ori": trans.cta_ori.acc_number,
                        "banco_ori": trans.cta_ori.bank_id.code_sat,
                        "monto": trans.monto,
                        "cta_dest": trans.cta_dest.acc_number,
                        "banco_dest": trans.cta_dest.bank_id.code_sat,
                        "fecha": trans.fecha,
                        "benef": trans.cta_dest.partner_id.name,
                        "rfc": trans.cta_ori.partner_id.vat if trans.move_line_id.move_id.tipo_poliza == '1' else trans.cta_dest.partner_id.vat
                    }
                    if trans.cta_ori.bank_id.extranjero:
                        vals["banco_ori_ext"] = trans.cta_ori.bank_id.name
                    if trans.cta_dest.bank_id.extranjero:
                        vals["banco_dest_ext"] = trans.cta_dest.bank_id.name
                    if trans.moneda_id:
                        vals.update({
                            "moneda": trans.moneda_id.name,
                            "tip_camb": trans.tipo_cambio
                        })
                    transaccion["transferencias"].append(vals)
                #-----------------------------------------------------------                    
                for met in move_line.otros_metodos_ids:
                    vals = {
                        "met_pago": met.metodo_id.code,
                        "fecha": met.fecha,
                        "benef": met.benef_id.name,
                        "rfc": met.benef_id.vat,
                        "monto": met.monto
                    }
                    if met.moneda_id:
                        vals.update({
                            "moneda": met.moneda_id.name,
                            "tip_camb": met.tipo_cambio
                        })
                    transaccion["otros_metodos"].append(vals)
                #-----------------------------------------------------------                    
                for comp in move_line.comprobantes_ids:
                    vals = {
                        "uuid": comp.uuid,
                        "monto": comp.monto,
                        "rfc": comp.rfc
                    }
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    transaccion["comprobantes"].append(vals)
                #-----------------------------------------------------------                    
                for comp in move_line.comprobantes_cfd_cbb_ids:
                    vals = {
                        "folio": comp.uuid,
                        "monto": comp.monto,
                        "rfc": comp.rfc
                    }
                    if comp.serie:
                        vals["serie"] = self.serie
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    transaccion["comprobantes"].append(vals)
                #-----------------------------------------------------------                    
                for comp in move_line.comprobantes_ext_ids:
                    vals = {
                        "num": comp.num,
                        "monto": comp.monto,
                    }
                    if comp.tax_id: vals["tax_id"] = comp.tax_id
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    transaccion["comprobantes"].append(vals)
                poliza["transacciones"].append(transaccion)
            data["polizas"].append(poliza)

        fname = '{0}{1}{2}PL'.format(self.company_id.partner_id.vat or '', data.get('ano'), data.get('mes'))
        ctx = {
            'fname': fname+'.xml',
            'version': vce,
            'xml_file': 'xml_polizas.xml',
            'xml_xsd': 'PolizasPeriodo_%s.xsd'%(vce),
            'xml_xslt': 'PolizasPeriodo_%s.xslt'%(vce),
        }
        datas={
            "data": data,
            "ctx": ctx
        }
        self.with_context(**ctx)._save_xml(data)
        return self.with_context(**ctx)._return_action()



    # XML AUXILIAR DE FOLIOS
    def action_xml_aux_folios(self):
        self.ensure_one()
        context = dict(self._context)

        model_data = self.env['ir.model.data']
        code_cheque = model_data.get_object("contabilidad_electronica", "metodo_pago_2").code
        code_transferencia = model_data.get_object("contabilidad_electronica", "metodo_pago_3").code

        company_id = self.env.user.company_id
        vce = company_id.conta_elect_version or '1_3'

        date_object = datetime.datetime.strptime(self.date_today, '%Y-%m-%d')
        last_day = calendar.monthrange(date_object.year,date_object.month)[1]
        data = {
            'mes': self._get_fiscalyear_month(),
            'ano': self._get_fiscalyear(),
            'rfc': self.env.user.company_id.vat,
            'tipo_solicitud': self.tipo_solicitud,
            'detalles': [],
            'version': vce
        }
        
        if self.num_orden: data['num_orden'] = self.num_orden
        if self.num_tramite: data['num_tramite'] = self.num_tramite
        for line in self.get_polizas_lines():
            poliza = {
                "num": "%s-%s"%(line.tipo_poliza, line.name),
                "fecha": line.date,
                "concepto": line.ref or line.name,
                "comprobantes": [],
                "comprobantes_cfd_cbb": [],
                "comprobantes_ext": []
            }
            uuids = []
            for move_line in line.line_ids:
                metodo_pago = False
                if move_line.transferencias_ids:
                    metodo_pago = code_transferencia
                elif move_line.cheques_ids:
                    metodo_pago = code_cheque
                elif move_line.otros_metodos_ids:
                    metodo_pago = move_line.otros_metodos_ids[0].metodo_id.code
                for comp in move_line.comprobantes_ids:
                    if comp.uuid in uuids:
                        continue
                    uuids.append(comp.uuid)
                    vals = {
                        "uuid": comp.uuid,
                        "monto": comp.monto,
                        "rfc": comp.rfc
                    }
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    if metodo_pago:
                        vals.update({"MetPagoAux": metodo_pago})
                    poliza["comprobantes"].append(vals)
                #-----------------------------------------------------------
                for comp in move_line.comprobantes_cfd_cbb_ids:
                    vals = {
                        "folio": comp.uuid,
                        "monto": comp.monto,
                        "rfc": comp.rfc
                    }
                    if comp.serie:
                        vals["serie"] = comp.serie
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    if metodo_pago:
                        vals.update({"MetPagoAux": metodo_pago})
                    poliza["comprobantes_cfd_cbb"].append(vals)
                #-----------------------------------------------------------                    
                for comp in move_line.comprobantes_ext_ids:
                    vals = {
                        "num": comp.num,
                        "monto": comp.monto,
                    }
                    if comp.tax_id: vals["tax_id"] = comp.tax_id
                    if comp.moneda_id:
                        vals.update({
                            "moneda": comp.moneda_id.name,
                            "tip_camb": comp.tipo_cambio
                        })
                    if metodo_pago:
                        vals.update({"MetPagoAux": metodo_pago})
                    poliza["comprobantes_ext"].append(vals)
            if len(poliza["comprobantes"]) > 0:
                data["detalles"].append(poliza)
        fname = '{0}{1}{2}XF'.format(self.company_id.partner_id.vat or '', data.get('ano'), data.get('mes'))
        ctx = {
            'version': vce,
            'xml_file': 'xml_aux_folios.xml',
            'xml_xsd': 'AuxiliarFolios_%s.xsd'%(vce),
            'xml_xslt': 'AuxiliarFolios_%s.xslt'%(vce),
            'fname': fname+'.xml'
        }
        datas={
            "data": data,
            "ctx": ctx
        }
        self.with_context(**ctx)._save_xml(data)
        return self.with_context(**ctx)._return_action()





    @api.multi
    def action_xml_aux_cuentas(self):
        self.ensure_one()
        context = dict(self._context)
        if not self.tipo_solicitud:
            raise UserError('Favor de indicar el tipo de solicitud')
        
        company_id = self.env.user.company_id
        vce = company_id.conta_elect_version or '1_3'

        date_object = datetime.datetime.strptime(self.date_today, '%Y-%m-%d')
        last_day = calendar.monthrange(date_object.year,date_object.month)[1]
        data = {
            'mes': self._get_fiscalyear_month(),
            'ano': self._get_fiscalyear(),
            'rfc': self.env.user.company_id.vat,
            'tipo_solicitud': self.tipo_solicitud,
            'cuentas': [],
            'version': vce
        }
        if self.num_orden: data['num_orden'] = self.num_orden
        if self.num_tramite: data['num_tramite'] = self.num_tramite

        ctx = {
            'date_from': '%s-%s-01'%(date_object.year, date_object.month),
            'date_to': '%s-%s-%s'%(date_object.year, date_object.month, last_day),
            'balanza': True
        }
        move_line_obj = self.env['account.move.line']
        cod_agrupador = self.env['contabilidad_electronica.codigo.agrupador']
        balanza_lines = cod_agrupador.with_context(**ctx).get_codigo_agrupador()
        balanza_lines.sort(key=lambda x: x["codigo"])
        for line in balanza_lines:
            cuenta = {
                'inicial': line['inicial'],
                'final': line['final'],
                'codigo': line['codigo'],
                'descripcion': line['descripcion'],
                'transacciones': []
            }

            transacciones_ids = move_line_obj.search(['&', 
                                    ('date','>=',self.date_from), 
                                    ('date','<=',self.date_to), 
                                    ('company_id', '=', self.company_id.id),
                                    ('account_id', '=', line['id']),
                                ])
            for t in transacciones_ids:
                cuenta["transacciones"].append({
                    'fecha': t.date, 
                    'num': "%s-%s"%(t.move_id.tipo_poliza, t.move_id.name),
                    'debe': t.debit,
                    'haber': t.credit,
                    'concepto': t.name
                })
            if len(cuenta["transacciones"]) > 0:
                data["cuentas"].append(cuenta)

        fname = '{0}{1}{2}XC'.format(self.company_id.partner_id.vat or '', data.get('ano'), data.get('mes'))
        ctx = {
            'version': vce,
            'xml_file': 'xml_aux_cuentas.xml',
            'xml_xsd': 'AuxiliarCtas_%s.xsd'%(vce),
            'xml_xslt': 'AuxiliarCtas_%s.xslt'%(vce),
            'fname': fname+'.xml'
        }
        datas={
            "data": data,
            "ctx": ctx
        }
        self.with_context(**ctx)._save_xml(data)
        return self.with_context(**ctx)._return_action()


    @api.multi
    def _return_action(self):
        self.ensure_one()
        context = dict(self._context)
        data_obj = self.env['ir.model.data']
        view = data_obj.xmlid_to_res_id('contabilidad_electronica.wizard_generar_xmls_form')
        return {
             'name': _('Generar XMLs'),
             'type': 'ir.actions.act_window',
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'contabilidad_electronica.wizard.generar.xmls',
             'views': [(view, 'form')],
             'view_id': view,
             'target': 'new',
             'res_id': self.id,
             'context': context,
         }


    @api.multi
    def _save_xml(self, datas):
        self.ensure_one()
        cfdi = self.env['account.cfdi']
        message = ""
        # res = cfdi.with_context(**datas).contabilidad(self)
        try:
            res = cfdi.with_context(**datas).contabilidad(self)
            if res.get('message'):
                message = res['message']
            else:
                return self.get_process_data(res.get('result'))
        except ValueError, e:
            message = str(e)
        except Exception, e:
            message = str(e)
        if message:
            message = message.replace("(u'", "").replace("', '')", "")
            cfdi.action_raise_message("%s "%( message.upper() ))
            return False
        return True

    def get_process_data(self, res):
        context = dict(self._context)
        vals = {
            'xml': res.get("xml"), 
            'fname': context.get('fname'), 
            'period_id': self._get_fiscalyear_month(),
            'fiscalyear': self._get_fiscalyear(),
        }
        self.write(vals)