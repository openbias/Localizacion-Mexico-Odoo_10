# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from json import dumps, loads


class validar_facturas(models.TransientModel):
    _name = "validar.facturas"

    xml = fields.Binary(string="XML")
    pdf = fields.Binary(string="PDF")
    reporte_validation_xml = fields.Html("Validar XML")
    message_validation_xml = fields.Html("Validar XML")
    codigo = fields.Char(string="Codigo Estatus")
    estado = fields.Char(string="Estado")
    uuid = fields.Char(string="UUID")
    uui_duplicado = fields.Boolean(string="UUID Duplicado", default=False)
    act_next = fields.Boolean(string="Continuar", default=False)
    moneda = fields.Many2one("res.currency", string="Moneda")
    product_id = fields.Many2one("product.product", string=u"Producto que aparecerá en la factura")
    partner_id = fields.Many2one("res.partner", string=u"Proveedor")
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True,
        default=lambda self: self.env['res.company']._company_default_get('validar.facturas'))

    # mensajes = fields.Text(string="Mensajes")
    # codigo = fields.Char(string="Codigo Estatus")
    # estado = fields.Char(string="Estado")
    # next = fields.Boolean(string="Continuar", default=False)
    # 
    # validar_partidas = fields.Boolean(string="Validar partidas", default=True)
    # total_xml = fields.Float(string="Total xml")
    # total_fac = fields.Float(string="Total factura")
    # all_ok = fields.Boolean(string="Todo bien")
    # lines = fields.One2many("validar_facturas.subir.factura.line", "wizard_id", string="Partidas")
    # show_lines = fields.Boolean(string="Show lines", default=False)

    
    @api.multi
    def action_validar_facturas(self):
        self.ensure_one()
        context = dict(self._context)
        cfdi = self.env['account.cfdi']
        message = ""
        # res = cfdi.validate(self)
        # if res.get('message'):
        #     message = res['message']
        # else:
        #     return self.get_process_data(res.get('result'))
        try:
            res = cfdi.validate(self)
            if res.get('message'):
                message = res['message']
            else:
                return self.with_context(context=context).get_process_data(res.get('result'))
        except ValueError, e:
            message = str(e)
        except Exception, e:
            message = str(e)
        if message:
            message = message.replace("(u'", "").replace("', '')", "")
            cfdi.action_raise_message("%s "%( message.upper() ))
            return False
        return True


    def get_process_data(self, datas):
        self.ensure_one()
        context = dict(self._context)
        context["xml_datas"] = datas
        vals = {
            'codigo': datas.get("cod_estatus", ""),
            'estado': datas.get("estado", ""),
            'message_validation_xml': "", 
            'reporte_validation_xml': "",
            'act_next': False
        }
        if context.get("inv_create", False):
            vals["act_next"] = True
        validar_xml = ""
        xml_datas = self._get_xml_datas(loads(datas["xml_datas"]))
        for inv in self.env["account.invoice"].search(['|', ('uuid', '=', xml_datas.get("uuid")), ('uuid', '=', xml_datas.get("uuid").replace("-",""))]):
            validar_xml += """ <br /> <br /> <p> UUID Duplicado en Factura : %s </p>"""%( inv.name )
            raise UserError("Ya se tiene en el sistema una factura con el UUID %s - %s "%(xml_datas.get("uuid"), (inv.name or inv.reference)))

        partner_id = self.env['res.partner'].search([('vat', '=', xml_datas.get("rfc_emisor"))], limit=1)
        if not partner_id:
            raise UserError(u"No se encontro en el sistema un proveedor con el RFC %s"%xml_datas.get("rfc_emisor"))

        partner_company_id = self.env['res.partner'].search([('vat', '=', xml_datas.get("rfc_receptor"))], limit=1)
        if not partner_company_id:
            raise UserError(u"El RFC no corresponde a la Empresa %s"%xml_datas.get("rfc_receptor"))

        vals["reporte_validation_xml"] = self._reporte_validacion_xml(xml_datas)
        vals["message_validation_xml"] = validar_xml
        vals["partner_id"] = partner_id.id
        vals["uuid"] = xml_datas.get("uuid")
        self.write(vals)
        data_obj = self.env['ir.model.data']
        view_name = 'validar_facturas.validar_facturas_crear_form'
        view = data_obj.xmlid_to_res_id(view_name)
        return {
            'name': _('Subir XML y PDF'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'validar.facturas',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'res_id': self.id,
            'context': context,
        }

    def _get_xml_datas(self, datas):
        ns = "{http://www.sat.gob.mx/cfd/3}"
        ns1 = "{http://www.sat.gob.mx/TimbreFiscalDigital}"
        d = datas.get("%sComprobante"%ns)
        emisor = d.get("%sEmisor"%ns)
        receptor = d.get("%sReceptor"%ns)
        timbre = d.get("%sComplemento"%ns) and d["%sComplemento"%ns].get("%sTimbreFiscalDigital"%ns1)
        uuid = timbre.get("@UUID") or ""
        nombre_emisor = emisor.get("@Nombre", "").encode('utf-8').decode('utf-8') or emisor.get("@nombre", "").encode('utf-8').decode('utf-8') or ""
        nombre_receptor = receptor.get("@Nombre", "").encode('utf-8').decode('utf-8') or receptor.get("@nombre", "").encode('utf-8').decode('utf-8') or ""
        res = {
            'importe_total': d.get("@Total") or d.get("@total"),
            'version': d.get("@Version") or d.get("@version"),
            'tipo_comprobante': d.get("@TipoDeComprobante") or d.get("@tipoDeComprobante") or "",
            'certificado_emisor': d.get("@NoCertificado") or d.get("@noCertificado") or "",
            'fecha_emision': d.get("@Fecha") or d.get("@fecha"),
            'nombre_emisor': nombre_emisor,
            'rfc_emisor': u"%s"%(emisor.get("@Rfc") or emisor.get("@rfc") or ""),
            'nombre_receptor': nombre_receptor,
            'rfc_receptor': u"%s"%(receptor.get("@Rfc") or receptor.get("@rfc") or ""),
            'certificado_sat': timbre.get("@noCertificadoSAT") or "",
            'fecha_certificacion': timbre.get("@FechaTimbrado") or "",
            'uuid': uuid,
        }
        return res

    def _reporte_validacion_xml(self, xml_datas):
        validar_xml = u"""
            <table class="small"  width="95%" style="border-collapse: separate; border-spacing: 0 0px; padding: 0px; padding-top: 0px; padding-bottom: 0px; " cellpadding="0" cellspacing="0" >
                <tbody>
                    <tr><td colspan="2" align="center" bgcolor="#dfe1d2"><h2>Reporte de validación</h2></td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Versión:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{version}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Tipo Comprobante:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{tipo_comprobante}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Certificado SAT:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{certificado_sat}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Certificado Emisor:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{certificado_emisor}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Fecha Emisión:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{fecha_emision}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Fecha Certificación:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{fecha_certificacion}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">UUID:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{uuid}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Importe Total:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{importe_total}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">RFC Emisor:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{rfc_emisor}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Nombre Emisor:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{nombre_emisor}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">RFC Receptor:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{rfc_receptor}</td></tr>
                    <tr><td class="small" style="color:black; font-weight:bold; border-bottom: 1px solid #dfe1d2;" width="25%">Nombre Receptor:</td><td width="75%" style="border-bottom: 1px solid #dfe1d2;">{nombre_receptor}</td></tr> 
                </tbody>
            </table>
            <br />
            <br />
        """.format(**xml_datas)
        return validar_xml


    @api.multi
    def action_create_invoice(self):
        self.ensure_one()
        context = dict(self._context)
        if context.get("inv_create", False):
            data = self.get_invoice_data()
            Invoice = self.env['account.invoice']
            data["currency_id"] = self.moneda.id
            data["creada_de_xml"] = True
            invoice_id = Invoice.create(data)
            self.with_context(invoice_id=invoice_id.id).write_att_values()
            invoice_id.compute_taxes()
            return {
                'view_mode': 'form',
                'view_type': 'form',
                'name': 'Invoice',
                'res_model': 'account.invoice',
                'res_id': invoice_id.id,
                'type': 'ir.actions.act_window',
                'context': context,
                'domain': [],
            }
        else:
            invoice_id = context.get('active_id')
            datas = self.get_invoice_data()
            vals = {
                "reference": datas.get("reference", ""),
                "supplier_invoice_number": datas.get("supplier_invoice_number", ""),
                "hora_factura": datas.get("hora_factura", ""),
                "date_invoice": datas.get("date_invoice"),
                "uuid": datas.get("uuid")
            }
            Inv = self.env['account.invoice'].browse(invoice_id)
            Inv.write(vals)
            self.with_context(invoice_id=invoice_id).write_att_values()
        return True


    @api.multi
    def get_invoice_data(self):
        context = self._context
        datas = context["xml_datas"]

        xml_datas = loads(datas["xml_datas"])

        Journal = self.env['account.journal']
        Partner = self.env['res.partner']
        Product = self.env['product.product']
        Umo = self.env['product.uom']
        Fpos = self.env['account.fiscal.position']
        InvoiceLine = self.env['account.invoice.line']
        IrValues = self.env['ir.values']
        
        uid_company_id = self.env.user.company_id.id
        journal_id = Journal.search([('type', '=', 'purchase'), ('company_id', '=', uid_company_id)], limit=1)
        data = {
            'type': 'in_invoice',
            'journal_id': journal_id and journal_id.id or False
        }

        ns = "{http://www.sat.gob.mx/cfd/3}"
        ns1 = "{http://www.sat.gob.mx/TimbreFiscalDigital}"
        d = xml_datas.get("%sComprobante"%ns)
        emisor = d.get("%sEmisor"%ns)
        receptor = d.get("%sReceptor"%ns)
        timbre = d.get("%sComplemento"%ns) and d["%sComplemento"%ns].get("%sTimbreFiscalDigital"%ns1)
        
        uuid = timbre.get("@UUID") or ""
        fecha = d.get("@Fecha") or d.get("@fecha") or ""
        folio = d.get("@Folio") or d.get("@folio") or ""
        descuento = d.get("@Descuento") or d.get("@descuento") or 0.0
        total = d.get("@Total") or d.get("@total") or 0.0
        version = d.get("@Version") or d.get("@version") or 0.0

        data["date_invoice"] = fecha.split("T")[0]
        data["hora_factura"] = fecha.split("T")[1]
        fpos = False
        if folio:
            data["supplier_invoice_number"] = folio
            data["reference"] = folio
        descuento = descuento
        data["check_total"] = total

        last_account_id = None
        last_account_id = self.product_id.property_account_expense_id and self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id.id

        data["partner_id"] = self.partner_id.id
        data["account_id"] = self.partner_id.property_account_payable_id.id
        data["uuid"] = uuid
        if d.get("%sConceptos"%ns):
            conceptos = d["%sConceptos"%ns].get("%sConcepto"%ns)
            if type(conceptos) is dict:
                conceptos = [conceptos]
        for con in conceptos:
            descuento = con.get("@Descuento") or con.get("@descuento") or 0.0
            taxes = [(4,tax.id) for tax in self.product_id.supplier_taxes_id]
            line_vals = {}
            line_vals["product_id"] = self.product_id.id
            line_vals['invoice_line_tax_ids'] = taxes
            line_vals["account_id"] = last_account_id
            line_vals["name"] = con.get("@Descripcion") or con.get("@descripcion") or ""
            line_vals["quantity"] = con.get("@Cantidad") or con.get("@cantidad") or 0.0
            line_vals["price_unit"] = con.get("@ValorUnitario") or con.get("@valorUnitario") or 0.0
            if descuento:
                line_vals["discount"] = descuento
            if self.product_id.uom_id:
                line_vals["uos_id"] = self.product_id.uom_id.id
            data.setdefault("invoice_line_ids", []).append((0,0,line_vals))
        return data

    @api.multi
    def write_att_values(self):
        context = dict(self._context)
        invoice_id = context.get('invoice_id')
        att_obj = self.env['ir.attachment']
        xml_att_values = {
          'name': self.uuid + ".xml",
          'datas': self.xml,
          'datas_fname': self.uuid + ".xml",
          'description': self.uuid,
          'res_model': "account.invoice",
          'res_id': invoice_id,
          'type': 'binary'
        }
        pdf_att_values = {
            'name': self.uuid + ".pdf",
            'datas': self.pdf,
            'datas_fname': self.uuid + ".pdf",
            'description': self.uuid,
            'res_model': "account.invoice",
            'res_id': invoice_id,
            'type': 'binary'
        }
        att_obj.create(xml_att_values)
        att_obj.create(pdf_att_values)
        return True