# -*- coding: utf-8 -*-

import base64
from xml.dom import minidom
from xml.dom.minidom import parse, parseString


import odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ['mail.thread', 'account.move.line', 'account.cfdi']

    uuid = fields.Char(string='Timbre fiscal', related='payment_id.cfdi_timbre_id.name')
    date_invoice = fields.Date(string='Invoice Date')

    {u'lang': u'es_MX', u'default_partner_type': u'customer', u'tz': u'America/Monterrey', u'uid': 1, u'default_payment_type': u'inbound', 
     u'params': {u'menu_id': 105, u'view_type': u'form', u'_push_me': False, u'action': 126, u'model': u'account.payment', u'id': 409}}


    @api.multi
    def remove_move_reconcile(self):
        """ Undo a reconciliation """
        if not self:
            return True

        invoice_id = self._context.get('invoice_id')
        if invoice_id:
            for account_move_line in self:
                if account_move_line.payment_id.cfdi_timbre_id:
                    msg = "NOTA: \n"
                    msg += "No es puede romper conciliacion a un CFDI de PAGOS \n"
                    msg += "Debes cancelar el Pago %s"%(account_move_line.payment_id.name)
                    raise UserError(msg)

        res = super(AccountMoveLine, self).remove_move_reconcile()
        return res

    @api.multi
    def get_xml(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            xml_id = self.env["ir.attachment"].search([('res_model', '=', 'cfdi.timbres.sat'), ('res_id', '=', self.payment_id.cfdi_timbre_id.id), ('type', '=', 'binary'), ('name', 'ilike', '%s.xml'%(self.uuid) )])
            url = '/web/content/%s?download=true'%(xml_id.id)
            return {
                'type': 'ir.actions.act_url',
                'url':url,
                'nodestroy': True
            }
        else:
            raise UserError("No es una Factura CFDI de Pago")

    @api.multi
    def get_pdf(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            return self.env['report'].get_action(self.payment_id.cfdi_timbre_id, 'complemento_pagos.report_cfdipagosmx')
        else:
            raise UserError("No es una Factura CFDI de Pago")

    @api.multi
    def get_email(self):
        self.ensure_one()
        if self.payment_id and self.payment_id.cfdi_timbre_id:
            template = self.env.ref('complemento_pagos.email_template_payment_receipt', False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='account.payment',
                default_res_id=self.payment_id.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
                mark_invoice_as_sent=True,
                cfdi_timbre_id=self.payment_id.cfdi_timbre_id.id,
                custom_layout="complemento_pagos.email_notification_paynow"
            )
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError("No es una Factura CFDI de Pago")

    @api.multi
    def get_xml_cfdi(self):
        nodosPagos = []
        timbreAtrib = {}
        compAtrib = {}
        receptorAtrib = {}
        emisorAtrib = {}
        xml = False
        att_obj = self.env['ir.attachment']
        for rec in self:
            att_ids = att_obj.search([('res_model', '=', 'account.move.line'), ('res_id', '=', rec.id), ('type', '=', 'binary')])
            for att_id in att_ids:
                xml = att_id.datas
                cfdi = base64.b64decode(att_id.datas)
                xmlDoc = parseString(cfdi)
                nodes = xmlDoc.childNodes
                comprobante = nodes[0]
                compAtrib = dict(comprobante.attributes.items())

                emisor = comprobante.getElementsByTagName('cfdi:Emisor')
                emisorAtrib = dict(emisor[0].attributes.items())

                receptor = comprobante.getElementsByTagName('cfdi:Receptor')
                receptorAtrib = dict(receptor[0].attributes.items())

                complementos = comprobante.getElementsByTagName('cfdi:Complemento')
                for comp in complementos:
                    timbreFiscal = comp.getElementsByTagName('tfd:TimbreFiscalDigital')
                    for timbre in timbreFiscal:
                        timbreAtrib = dict(timbre.attributes.items())

                    pagos10 = comp.getElementsByTagName('pago10:Pagos')
                    for pago10 in pagos10:
                        pagos = pago10.getElementsByTagName('pago10:Pago')
                        for pago in pagos:
                            pagoAtrib = dict(pago.attributes.items())
                            doctosAtrib = []
                            rels = pago.getElementsByTagName('pago10:DoctoRelacionado')
                            for rel in rels:
                                relAtrib = dict(rel.attributes.items())
                                doctosAtrib.append(relAtrib)
                            nodosPagos.append({
                                'pagosAtrib': pagoAtrib,
                                'doctosAtrib': doctosAtrib
                            })
        return {
            'compAtrib': compAtrib,
            'receptorAtrib': receptorAtrib,
            'emisorAtrib': emisorAtrib,
            'nodosPagos': nodosPagos,
            'timbreAtrib': timbreAtrib,
            'xml': xml
        }


    @api.multi
    def getElectronicPayment(self):
        Timbre = self.env["cfdi.timbres.sat"]
        Attachment = self.env['ir.attachment']
        for moveline_id in self:
            if moveline_id.payment_id:
                payment_id = moveline_id.payment_id
                attrs = moveline_id.get_xml_cfdi()
                if attrs and attrs.get("compAtrib") and attrs["compAtrib"].get("Sello"):
                    xml = attrs["xml"]
                    compAtrib = attrs["compAtrib"]
                    timbreAtrib = attrs["timbreAtrib"]
                    emisorAtrib = attrs["emisorAtrib"]
                    receptorAtrib = attrs["receptorAtrib"]
                    uuid = timbreAtrib.get('UUID')
                    timbre_ids = Timbre.search([('name', '=', uuid)])
                    vals = {
                        "name": timbreAtrib.get('UUID'),
                        "cfdi_supplier_rfc": emisorAtrib.get('Rfc', ''),
                        "cfdi_customer_rfc": receptorAtrib.get('Rfc', ''),
                        "cfdi_amount": float(timbreAtrib.get('Total', '0.0')),
                        "cfdi_certificate": compAtrib.get('NoCertificado', ''),
                        "cfdi_certificate_sat": timbreAtrib.get('NoCertificadoSAT', ''),
                        "time_invoice": compAtrib.get('Fecha', ''),
                        "time_invoice_sat": timbreAtrib.get('FechaTimbrado', ''),
                        'currency_id': payment_id.currency_id and payment_id.currency_id.id or False,
                        'cfdi_type': compAtrib.get('TipoDeComprobante', 'P'),
                        "cfdi_pac_rfc": timbreAtrib.get('RfcProvCertif', ''),
                        "cfdi_cadena_ori": "",
                        'cfdi_cadena_sat': self.cadena_sat,
                        'cfdi_sat_status': "valid",
                        'journal_id': payment_id.journal_id.id,
                        'partner_id': payment_id.partner_id.id,
                        'company_id': payment_id.company_id.id,
                        'test': moveline_id.test
                    }
                    if timbre_ids:
                        timbre_id = timbre_ids.sudo().write(vals)
                    if not timbre_ids:
                        timbre_id = Timbre.sudo().create(vals)
                        xname = "%s.xml"%uuid
                        attachment_values = {
                            'name':  xname,
                            'datas': xml,
                            'datas_fname': xname,
                            'description': 'Comprobante Fiscal Digital',
                            'res_model': 'cfdi.timbres.sat',
                            'res_id': timbre_id.id,
                            'type': 'binary'
                        }
                        Attachment.sudo().create(attachment_values)
                        payment_id.sudo().write({
                            'cfdi_timbre_id': timbre_id.id
                        })

        return True

