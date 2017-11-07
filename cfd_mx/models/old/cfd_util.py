# -*- coding: utf-8 -*-

import requests
from requests import Request, Session

from datetime import date, datetime
from pytz import timezone
import json

class CfdiUtils:

    def __init__(self, obj):
        cia = obj.company_id
        self.obj = obj 
        self.host = cia.cfd_mx_host
        self.port = cia.cfd_mx_port
        self.db = cia.cfd_mx_db

    def stamp(self):
        cia = self.obj.company_id
        conceptos = self.get_info_comprobante_conceptos(self.obj)
        cfdi_datas = {
            'comprobante': self.get_info_comprobante(self.obj),
            'emisor': self.get_info_comprobante_emisor(self.obj),
            'receptor': self.get_info_comprobante_receptor(self.obj),
            'conceptos': conceptos,
            'impuestos': self.get_info_comprobante_impuestos(conceptos),
            'addenda': self.obj.get_comprobante_addenda(),
            'vat': cia.partner_id.vat,
            'cfd': self.get_info_pac(self.obj),
            'db': self.db
        }
        self.datas = json.dumps(cfdi_datas, sort_keys=True, indent=4, separators=(',', ': '))
        url = '%s/stamp/'%(self.host)
        if self.port:
            url = '%s:%s/stamp/'%(self.host, self.port)
        params = {"context": {},  "post":  self.datas }
        res_datas =  self.action_server(url, params)
        return res_datas

    def cancel(self):
        cia = self.obj.company_id
        url = '%s/cancel/'%(self.host)
        if self.port:
            url = '%s:%s/cancel/'%(self.host, self.port)
        cfdi_datas = {
            'db': self.db,
            'uuid': self.obj.uuid,
            'vat': cia.partner_id.vat,
            'test': cia.cfd_mx_test,
            'cfd': self.get_info_pac(self.obj),
            'noCertificado': self.obj.noCertificado
        }
        self.datas = json.dumps(cfdi_datas, sort_keys=True, indent=4, separators=(',', ': '))
        params = {"context": {},  "post":  self.datas}
        res_datas =  self.action_server(url, params)
        return res_datas

    def action_server(self, url, params):
        s = Session()
        if self.port:
            s.get('%s:%s/web?db=%s'%(self.host, self.port, self.db) )
        else:
            s.get('%s/web?db=%s'%(self.host, self.db))
        headers = {
            'Content-Type':'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0',
            'Referer' : url
        }
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "id":0,
            "params": params
        }
        res = s.post(url, data=json.dumps(data), headers=headers)
        res_datas = res.json()
        print "res_datas", res_datas
        if res_datas.get('error'):
            return res_datas['error']
        if res_datas.get('result') and res_datas['result'].get('error'):
            return res_datas['result']['error']
        return res_datas

    def get_info_pac(self, obj):
        com_id = obj.company_id
        cfdi_datas = {
            'test': com_id.cfd_mx_test,
            'pac': com_id.cfd_mx_pac,
            'version': com_id.cfd_mx_version
        }
        return cfdi_datas

    def get_info_comprobante(self, obj):
        dp = obj.env['decimal.precision'].precision_get('Account')
        tz = obj.env.user.tz
        hora_factura_utc = datetime.now(timezone("UTC"))
        hora_factura_local = hora_factura_utc.astimezone(timezone(tz)).strftime("%H:%M:%S")
        if obj.currency_id.name == 'MXN':
            rate = 1.0
            nombre = obj.currency_id.nombre_largo or 'pesos'
        else:
            model_data = obj.env["ir.model.data"]
            mxn_rate = model_data.get_object('base', 'MXN').rate
            rate = (1.0 / obj.currency_id.rate) * mxn_rate
            nombre = obj.currency_id.nombre_largo or ''


        cfdi_comprobante = {
            "Folio": obj.number,
            "Fecha": str(obj.date_invoice) + "T" + hora_factura_local,
            "FormaPago": obj.formapago_id and obj.formapago_id.clave or "99",
            "CondicionesDePago": obj.payment_term_id and obj.payment_term_id.name or 'CONDICIONES',
            "Moneda": obj.currency_id.name,
            "Moneda_Nombre": nombre or '',
            "SubTotal": '%.2f'%(obj.price_subtotal_sat),
            "Total": '%.2f'%(obj.price_subtotal_sat - obj.price_discount_sat + obj.price_tax_sat),
            "TipoDeComprobante": obj.tipo_comprobante,
            "MetodoPago_Clave": obj.metodopago_id and obj.metodopago_id.clave or 'Pago en una sola exhibicion',
            "MetodoPago_Name": obj.metodopago_id and obj.metodopago_id.name or 'Pago en una sola exhibicion',
            "LugarExpedicion_Name": obj.journal_id and obj.journal_id.lugar or '',
            "LugarExpedicion_Clave": obj.journal_id and obj.journal_id.codigo_postal_id and obj.journal_id.codigo_postal_id.name or '',
            "Confirmacion": "",
            "NumCtaPago": '%s'%(obj.cuentaBanco or ''),
            "Descuento": '%.2f'%(0.0)
        }
        if obj.journal_id.serie:
            cfdi_comprobante['Serie'] = obj.journal_id.serie or ''
        if obj.price_discount_sat:
            cfdi_comprobante['Descuento'] = '%.2f'%(round(obj.price_discount_sat, dp))
        if obj.currency_id.name != 'MXN':
            cfdi_comprobante['TipoCambio'] = '%s'%(round(rate, 4))
        return cfdi_comprobante


    def get_info_comprobante_emisor(self, obj):
        partner_data = obj.company_id.partner_id
        emisor_attribs = {
            'rfc': partner_data.vat or "",
            'nombre': partner_data.name or "",
        }
        domicilio_attribs = {
            'calle': partner_data.street or "",
            'noExterior': partner_data.noExterior or "",
            'noInterior': partner_data.noInterior or "",
            'localidad': partner_data.city or "",
            'colonia': partner_data.street2 or "",
            'municipio': partner_data.city or "",
            'estado': partner_data.state_id and partner_data.state_id.name or "",
            'pais': partner_data.country_id and partner_data.country_id.name or "",
            'codigoPostal': partner_data.zip or "",
        }
        regimen_attribs = {
            'Regimen_Clave': partner_data.regimen_id and partner_data.regimen_id.clave or "",
            'Regimen_Name': partner_data.regimen_id and partner_data.regimen_id.name or ""
        }
        comprobante_emisor = {
            'emisor': emisor_attribs,
            'domicilioFiscal': domicilio_attribs,
            'regimenFiscal': regimen_attribs
        }
        return comprobante_emisor

    def get_info_comprobante_receptor(self, obj):
        partner_data = obj.partner_id
        receptor_attribs = {
            'rfc': partner_data.vat or "",
            'nombre': partner_data.name or "",
            'UsoCFDI': obj.usocfdi_id and obj.usocfdi_id.clave or ''
        }
        domicilio_attribs = {
            'calle': partner_data.street or "",
            'noExterior': partner_data.noExterior or "",
            'noInterior': partner_data.noInterior or "",
            'localidad': partner_data.city or "",
            'colonia': partner_data.street2 or "",
            'municipio': partner_data.city or "",
            'estado': partner_data.state_id and partner_data.state_id.name or "",
            'pais': partner_data.country_id and partner_data.country_id.name or "",
            'codigoPostal': partner_data.zip or "",
        }
        if partner_data.identidad_fiscal:
            receptor_attribs['NumRegIdTrib'] = partner_data.identidad_fiscal or ''
            domicilio_attribs['ResidenciaFiscal'] = partner_data.country_id.code_alpha3 or ''
        cfdi_receptor = {
            'receptor': receptor_attribs,
            'domicilioFiscal': domicilio_attribs,
        }
        return cfdi_receptor

    def get_info_comprobante_conceptos(self, obj):
        dp = obj.env['decimal.precision']
        dp_account = dp.precision_get('Account')
        dp_product = dp.precision_get('Product Price')
        conceptos = []
        for line in obj.invoice_line_ids:
            ClaveProdServ = '01010101'
            concepto_attribs = {
                'ClaveProdServ': line.product_id and line.product_id.clave_prodser_id and line.product_id.clave_prodser_id.clave or ClaveProdServ,
                'NoIdentificacion': line.product_id and line.product_id.default_code or '',
                'Descripcion': line.name.replace('[', '').replace(']', '') or '',
                'Cantidad': '%s'%(round(line.quantity, dp_account)),
                'ClaveUnidad': line.uom_id and line.uom_id.clave_unidadesmedida_id and line.uom_id.clave_unidadesmedida_id.clave or '',
                'Unidad': line.uom_id and line.uom_id.name or '',
                'ValorUnitario': '%.2f'%(round(line.price_unit, dp_product)),
                'Importe': '%.2f'%( line.price_subtotal_sat ),
                'Descuento': '%.2f'%( line.price_discount_sat ),
                'Impuestos': {
                    'Traslado': [],
                    'Retenciones': []
                }
            }
            for tax in line.invoice_line_tax_ids:
                tax_group = tax.tax_group_id
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                comp = tax.compute_all(price_unit, obj.currency_id, line.quantity, line.product_id, obj.partner_id)
                importe = comp['total_included'] - comp['total_excluded']
                TasaOCuota = '%.6f'%((round(abs(tax.amount), dp_account) / 100))
                impuestos = {
                    'Base': '%.2f'%(round( comp.get('base') , dp_account)),
                    'Impuesto': tax_group.cfdi_impuestos,
                    'TipoFactor': '%s'%(tax.cfdi_tipofactor),
                    'TasaOCuota': '%s'%(TasaOCuota),
                    'Importe': '%.2f'%(round(importe, dp_account))
                }
                if tax_group.cfdi_retencion:
                    concepto_attribs['Impuestos']['Retenciones'].append(impuestos)
                if tax_group.cfdi_traslado:
                    concepto_attribs['Impuestos']['Traslado'].append(impuestos)
            conceptos.append(concepto_attribs)
        cfdi_conceptos = conceptos
        return cfdi_conceptos

    def get_info_comprobante_impuestos(self, conceptos):
        TotalImpuestosRetenidos = 0.00
        TotalImpuestosTrasladados = 0.00
        traslado_attribs = {}
        for concepto in conceptos:
            for impuesto in concepto['Impuestos']:
                if impuesto == 'Retenciones':
                    for ret in concepto['Impuestos'][impuesto]:
                        TotalImpuestosRetenidos += ret['Importe']
                        if not ret['Impuesto'] in traslado_attribs.keys():
                            traslado_attribs[ ret['Impuesto'] ] = {
                                'Importe': '%s'%(0.0)
                            }
                        importe = traslado_attribs[ ret['Impuesto'] ]['Importe'] + ret['Importe']
                        traslado_attribs[ ret['Impuesto'] ] = {
                            'Impuesto': ret['Impuesto'],
                            'TipoFactor': ret['TipoFactor'],
                            'TasaOCuota': ret['TasaOCuota'],
                            'Importe': '%s'%(importe)
                        }
                if impuesto == 'Traslado':
                    for tras in concepto['Impuestos'][impuesto]:
                        TotalImpuestosTrasladados += float(tras['Importe'])
                        if not tras['Impuesto'] in traslado_attribs.keys():
                            traslado_attribs[ tras['Impuesto'] ] = {
                                'Importe': '%s'%(0.0)
                            }
                        importe = float(traslado_attribs[tras['Impuesto']]['Importe']) + float(tras['Importe'])
                        traslado_attribs[ tras['Impuesto'] ] = {
                            'Impuesto': tras['Impuesto'],
                            'TipoFactor': tras['TipoFactor'],
                            'TasaOCuota': tras['TasaOCuota'],
                            'Importe': '%.2f'%(importe)
                        }
        cfdi_impuestos = {
            'TotalImpuestosRetenidos': '%.2f'%(TotalImpuestosRetenidos),
            'TotalImpuestosTrasladados': '%.2f'%(TotalImpuestosTrasladados),
            'traslado_attribs': traslado_attribs
        }
        return cfdi_impuestos