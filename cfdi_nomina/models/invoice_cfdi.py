# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

from pytz import timezone
from datetime import datetime, date
from dateutil import relativedelta

import logging
logging.basicConfig(level=logging.INFO)

def getAntiguedad(date_from, date_to):
    FechaInicioRelLaboral = datetime.strptime(date_from, "%Y-%m-%d")
    FechaFinalPago = datetime.strptime(date_to, "%Y-%m-%d")
    FechaFinalPago = FechaFinalPago +relativedelta.relativedelta(days=+0)
    difference = relativedelta.relativedelta(FechaFinalPago, FechaInicioRelLaboral)

    years = difference.years
    months = difference.months
    days = difference.days

    logging.info("years %s "%years )
    logging.info("months %s "%months )
    logging.info("days %s "%days )

    p_diff = "P"
    if years > 0:
        p_diff += "%sY"%(years)
    if months > 0:
        p_diff += "%sM"%(months)
    if days > 0 or days==0:
        p_diff += "%sD"%(days)
    return p_diff
    
    p_diff = ""
    if (years <= 0 and months <= 0):
        logging.info("-- PD - Difference is %s year, %s months, %s days " %(years, months, days))
        p_diff = "P%sD"%(days)
        return p_diff

    if (years <= 0 and months > 0):
        logging.info("-- PMD - Difference is %s year, %s months, %s days " %(years, months, days))
        p_diff = "P%sM%sD"%(months, days)
        return p_diff

    if (years > 0 and months > 0):
        logging.info("-- PYMD - Difference is %s year, %s months, %s days " %(years, months, days))
        p_diff = "P%sY%sM%sD"%(years, months, days)
        return p_diff

    return p_diff

class AccountCfdi(models.Model):
    _name = 'account.cfdi'
    _inherit = "account.cfdi"

    ################################
    #
    # Nomina
    #
    ################################

    def nomina_info_relacionados(self):
        cfdi_relacionado = {}
        if self.cfdi_timbre_id:
            cfdi_relacionado["TipoRelacion"] = '04'
            cfdi_relacionado["uuid"] = self.cfdi_timbre_id.name
        return cfdi_relacionado


    def nomina_info_comprobante(self):
        rec = self.obj
        tz = rec.env.user.tz

        cfdi_comprobante = {
            "Version": "3.3",
            "Folio": rec._get_folio(),
            "Fecha": rec.date_invoice_cfdi,
            "SubTotal": 0,
            "Moneda": "MXN",
            "Total": 0,
            "TipoDeComprobante": "N",
            "FormaPago": "99",
            "MetodoPago": "PUE",
            "TipoCambio": "1",
            "LugarExpedicion": rec.journal_id.codigo_postal_id.name
        }
        if rec.journal_id.serie:
            cfdi_comprobante['Serie'] = rec.journal_id.serie or ''
        return cfdi_comprobante

    def nomina_info_emisor(self):
        obj = self.obj
        partner_data = obj.company_id.partner_id
        emisor_attribs = {
            'Rfc': partner_data.vat or "",
            'Nombre': partner_data.name or "",
            "RegimenFiscal": partner_data.regimen_id and partner_data.regimen_id.clave or ""
        }
        return emisor_attribs

    def nomina_info_receptor(self):
        obj = self.obj
        partner_data = obj.employee_id
        receptor_attribs = {
            'Rfc': partner_data.rfc or "",
            'Nombre': partner_data.nombre_completo or "",
            'UsoCFDI': 'G03'
        }
        return receptor_attribs

    def nomina_info_conceptos(self):
        cfdi_conceptos = []
        concepto_attribs = {
            "ClaveProdServ": "84111505",
            "Cantidad": 1,
            "ClaveUnidad": "ACT",
            "Descripcion": u"Pago de nómina"
        }
        cfdi_conceptos.append(concepto_attribs)
        return cfdi_conceptos


    def nomina_info_complemento(self):
        ctx = dict(self._context) or {}
        rec = self.obj
        empleado = rec.employee_id
        company = rec.company_id

        tz = self.env.user.tz
        fecha_utc =  datetime.now(timezone("UTC"))
        fecha_local = fecha_utc.astimezone(timezone(tz)).strftime("%Y-%m-%dT%H:%M:%S")

        # Atributos Nomina
        nomina_attribs = {
            "TipoNomina": rec.tipo_nomina,
            "FechaPago": rec.fecha_pago,
            "FechaInicialPago": rec.date_from,
            "FechaFinalPago": rec.date_to,
            "NumDiasPagados": "%d"%rec._get_days("WORK100")[0],
        }

        # Atributos Emisor
        emisor_attribs = {
            "RegistroPatronal": (empleado.registro_patronal_id and empleado.registro_patronal_id.name) or (company.registro_patronal_id and company.registro_patronal_id.name) or False
        }
        if company.partner_id.es_personafisica:
            emisor_attribs['Curp'] = company.partner_id.curp

        # Atributo Origin Recurso
        recurso_attribs = {}
        if rec.source_sncf:
            recurso_attribs = {
                'OrigenRecurso': rec.source_sncf
            }
            if rec.amount_sncf != 0.0:
                recurso_attribs['MontoRecursoPropio'] = rec.amount_sncf

        # Atributos Receptor
        banco = False
        num_cuenta = ""
        if empleado.bank_account_id:
            banco = empleado.bank_account_id and empleado.bank_account_id.bank_id.bic
            #Además, si no es CLABE asegurarse que tiene 10 posiciones la cuenta
            num_cuenta = num_cuenta[len(num_cuenta)-16:]
        # contract_id = empleado.contract_id
        fecha_alta = rec.contract_id.date_start or empleado.fecha_alta or False

        antiguedad = getAntiguedad(fecha_alta, rec.date_to)
        logging.info("----antiguedad %s --- %s --- %s  "%(antiguedad, fecha_alta, rec.date_to) )
        riesgo_puesto = (empleado.job_id and empleado.job_id.riesgo_puesto_id and empleado.job_id.riesgo_puesto_id.code) or (company.riesgo_puesto_id and company.riesgo_puesto_id.code) or False
        periodicidad_pago = (rec.periodicidad_pago_id and rec.periodicidad_pago_id.code) or (rec.contract_id.periodicidad_pago_id and rec.contract_id.periodicidad_pago_id.code) or ""
        # periodicidad_pago = rec.contract_id.periodicidad_pago_id and rec.contract_id.periodicidad_pago_id.code or ""
        receptor_attribs = {
            "Curp": empleado.curp or "",
            "TipoContrato": rec.contract_id.type_id and rec.contract_id.type_id.code or "",
            "TipoRegimen": rec.contract_id.regimen_contratacion_id and rec.contract_id.regimen_contratacion_id.code or "",
            "NumEmpleado": empleado.cod_emp or "",
            "PeriodicidadPago": periodicidad_pago,
            "ClaveEntFed": empleado.address_home_id and empleado.address_home_id.state_id.code or "",
            "Antiguedad": antiguedad
        }
        if empleado.imss:
            receptor_attribs['NumSeguridadSocial'] = empleado.imss
        if fecha_alta:
            receptor_attribs['FechaInicioRelLaboral'] = fecha_alta
        if empleado.sindicalizado:
            receptor_attribs['Sindicalizado'] = u"Sí"
        if empleado.tipo_jornada_id.code:
            receptor_attribs['TipoJornada'] = empleado.tipo_jornada_id.code
        if empleado.department_id:
            receptor_attribs['Departamento'] = empleado.department_id and empleado.department_id.name.replace("/", "")
        if empleado.job_id:
            receptor_attribs['Puesto'] = empleado.job_id and empleado.job_id.name
        if riesgo_puesto:
            receptor_attribs['RiesgoPuesto'] = riesgo_puesto
        if banco:
            receptor_attribs['Banco'] = banco
        if num_cuenta:
            receptor_attribs['CuentaBancaria'] = num_cuenta
        if empleado.sueldo_diario:
            receptor_attribs['SalarioBaseCotApor'] = "%.2f"%empleado.sueldo_diario
        if empleado.sueldo_imss:
            receptor_attribs['SalarioDiarioIntegrado'] = "%.2f"%empleado.sueldo_imss

        #--------------------
        # Percepciones
        #--------------------
        totalPercepciones = 0.0
        totalGravadoP = 0.0
        totalExentoP = 0.0
        totalSueldosP = 0.0
        totalSepIndem = 0.0
        totalJubilacion = 0.0
        percepciones = {}

        nodo_p = rec._get_lines_type('p')
        if nodo_p:
            percepciones = {
                "lines": [],
                "attrs": {
                    "TotalGravado": 0.0,
                    "TotalExento": 0.0,
                    "TotalSueldos": 0.0,
                }
            }
            for percepcion in nodo_p:
                tipo_percepcion, nombre_percepcion = rec._get_code(percepcion)
                tipo = percepcion.salary_rule_id.gravado_o_exento or 'gravado'
                gravado = percepcion.total if tipo == 'gravado' else 0
                exento = percepcion.total if tipo == 'exento' else 0
                if gravado + exento == 0:
                    continue
                nodo_percepcion = {
                    "TipoPercepcion": tipo_percepcion,
                    "Clave": tipo_percepcion,
                    "Concepto": nombre_percepcion.replace(".", "").replace("/", ""),
                    "ImporteGravado": "%.2f"%gravado,
                    "ImporteExento": "%.2f"%exento
                }
                totalGravadoP += gravado
                totalExentoP += exento
                if tipo_percepcion not in ("022", "023", "025", "039", "044"):
                    totalSueldosP += gravado + exento
                elif tipo_percepcion in ("022", "023", "025"):
                    totalSepIndem += gravado + exento
                elif tipo_percepcion in ("039", "044"):
                    totalJubilacion += gravado + exento

                #----------------
                # Nodo Horas extra
                #----------------
                horas_extras = {}
                if tipo_percepcion == '019':
                    tipo_horas = "01" #percepcion.salary_rule_id.tipo_horas.code or "01"
                    days_code = "EXTRA2" if tipo_horas == '01' else 'EXTRA3'
                    dias, horas = self._get_days(rec, days_code)
                    horas_extras = {
                        "Dias": "%d"%dias,
                        "TipoHoras": "%s"%tipo_horas,
                        "HorasExtra": "%d"%horas,
                        "ImportePagado": "%.2f"%(gravado + exento),
                    }

                percepciones['lines'].append({
                    "attrs": nodo_percepcion,
                    "horas_extras": horas_extras
                })

            percepciones["attrs"]['TotalGravado'] = "%.2f"%totalGravadoP
            percepciones["attrs"]['TotalExento'] = "%.2f"%totalExentoP
            percepciones["attrs"]['TotalSueldos'] = "%.2f"%totalSueldosP
            totalPercepciones = totalSueldosP + totalSepIndem + totalJubilacion

            if totalSepIndem:
                #-------------------
                # Nodo indemnización
                #-------------------
                ultimo_sueldo_mensual = empleado.sueldo_imss * 30
                percepciones["SeparacionIndemnizacion"] = {
                    'TotalPagado': "%.2f"%totalSepIndem,
                    'NumAñosServicio': empleado.anos_servicio,
                    'UltimoSueldoMensOrd': ultimo_sueldo_mensual,
                    'IngresoAcumulable': "%.2f"%min(totalSepIndem, ultimo_sueldo_mensual),
                    'IngresoNoAcumulable': "%.2f"%totalSepIndem - ultimo_sueldo_mensual
                }
                percepciones["attrs"]["TotalSeparacionIndemnizacion"] = "%.2f"%totalSepIndem

            if totalJubilacion:
                ultimo_sueldo_mensual = empleado.sueldo_imss * 30
                #-------------------
                # Nodo Jubilación
                #-------------------
                vals = {
                   'TotalUnaExhibición': "%.2f"%totalJubilacion,
                   'IngresoAcumulable': "%.2f"%min(totalJubliacion, ultimo_sueldo_mensual),
                   'IngresoNoAcumulable': "%.2f"%totalJubilacion - ultimo_sueldo_mensual
                }
                # Si es en parcialidades
                if tipo_percepcion == '044': 
                   del vals['TotalUnaExhibición'],
                   vals.update({
                      'TotalParcialidad': "%.2f"%totalJubilacion,
                      'MontoDiario': "%.2f"%empleado.retiro_paricialidad
                   })
                percepciones["JubilacionPensionRetiro"] = vals
                percepciones["attrs"]["TotalJubilacionPensionRetiro"] = "%.2f"%totalJubilacion

        #--------------------
        # Deducciones
        #--------------------
        totalDeducciones = 0.0
        totalD = 0.0
        retenido = 0.0
        deducciones = {}
        nodo_d = rec._get_lines_type('d')
        if nodo_d:
            lines_d = []
            attrs_d = {}
            for deduccion in nodo_d:
                tipo_deduccion, nombre_deduccion = rec._get_code(deduccion)
                if tipo_deduccion == '002':
                    retenido += deduccion.total
                else:
                    totalD += deduccion.total
                if deduccion.total == 0:
                    continue

                nodo_deduccion = {
                    "TipoDeduccion": tipo_deduccion,
                    "Clave": tipo_deduccion,
                    "Concepto": nombre_deduccion.replace(".", "").replace("/", "").replace("(", "").replace(")", ""),
                    "Importe": "%.2f"%abs(deduccion.total),
                }
                lines_d.append(nodo_deduccion)
            
            if totalD != 0.00:
                attrs_d["TotalOtrasDeducciones"] = "%.2f"%totalD
            if retenido != 0.00:
                attrs_d["TotalImpuestosRetenidos"] = "%.2f"%retenido
            # deducciones["attrs"]["TotalImpuestosRetenidos"] = "%.2f"%retenido
            if (lines_d and attrs_d):
                totalDeducciones = totalD + retenido
                deducciones = {
                    "lines": lines_d,
                    "attrs": attrs_d
                }


        #--------------------
        # Otros Pagos
        #--------------------
        totalOtrosPagos = 0.0
        nodo_o = rec._get_lines_type('o')
        otros_pagos = {}
        if nodo_o:
            otros_pagos = {
                "lines": []
            }
            for otro_pago in nodo_o:
                # if otro_pago.total == 0:
                #     continue

                tipo_otro_pago, nombre_otro_pago = rec._get_code(otro_pago)
                attrs = {
                    "TipoOtroPago": tipo_otro_pago,
                    "Clave": tipo_otro_pago,
                    "Concepto": nombre_otro_pago.replace(".", "").replace("/", "").replace("(", "").replace(")", ""),
                    "Importe": "%.2f"%abs(otro_pago.total)
                }
                totalOtrosPagos += otro_pago.total
                
                #--------------------
                # Subsidio al empleo
                #--------------------
                SubsidioAlEmpleo = {}
                CompensacionSaldosAFavor = {}
                if tipo_otro_pago == '002':
                    # otro_pago.total
                    total_SAEC = rec.get_salary_line_total('SAEC')
                    print('---------total SAEC ', total_SAEC)
                    SubsidioAlEmpleo = {
                        'SubsidioCausado': "%.2f"%abs(total_SAEC)
                    }
                
                #--------------------
                # Compensación anual
                #--------------------
                elif tipo_otro_pago == '004':
                   year = int(fecha_local.split("-")[0])
                   CompensacionSaldosAFavor = {
                       'SaldoAFavor': "%.2f"%abs(otro_pago.total),
                       'Año': "%s"%(year-1),
                       'RemanenteSalFav': 0
                   }
                otros_pagos['lines'].append({
                    "attrs": attrs,
                    "SubsidioAlEmpleo": SubsidioAlEmpleo,
                    "CompensacionSaldosAFavor": CompensacionSaldosAFavor
                })
            # if totalOtrosPagos > 0:
            nomina_attribs["TotalOtrosPagos"] = "%.2f"%totalOtrosPagos


        #----------------
        # Incapacidades
        #----------------
        nodo_i = rec._get_lines_type('i')
        incapacidades = {}
        if nodo_i:
            incapacidades = {
                "lines": []
            }
            for incapacidad in nodo_i:
                inca = rec._get_input(incapacidad)
                if inca != 0:
                    tipo_incapacidad, nombre_incapacidad = rec._get_code(incapacidad)
                    nodo_incapacidad = {
                        "DiasIncapacidad": "%d"%rec._get_input(incapacidad),
                        "TipoIncapacidad": tipo_incapacidad,
                        "ImporteMonetario": "%.2f"%abs(incapacidad.total),
                    }
                    incapacidades['lines'].append(nodo_incapacidad)
                    
        # **************** Llenado final de complemento **********
        nomina_attribs["TotalPercepciones"] = "%.2f"%totalPercepciones
        if totalDeducciones != 0.0:
            nomina_attribs["TotalDeducciones"] = "%.2f"%totalDeducciones

        # ***************** Conceptos y totales ******************
        importe = totalPercepciones + totalOtrosPagos
        subtotal = importe
        descuento = totalDeducciones
        total = subtotal - descuento

        self.cfdi_datas['conceptos'][0]["Importe"] = "%.2f"%importe
        self.cfdi_datas['conceptos'][0]["ValorUnitario"] = "%.2f"%importe
        if descuento:
            self.cfdi_datas['conceptos'][0]["Descuento"] = "%.2f"%descuento        

        self.cfdi_datas['comprobante']["Total"] = "%.2f"%total
        self.cfdi_datas['comprobante']["SubTotal"] = "%.2f"%subtotal
        if descuento:
            self.cfdi_datas['comprobante']["Descuento"] = "%.2f"%descuento
        res = {
            "nomina_attribs": nomina_attribs,
            "emisor_attribs": emisor_attribs,
            "recurso_attribs": recurso_attribs,
            "receptor_attribs": receptor_attribs,
            "percepciones": percepciones,
            "deducciones": deducciones,
            "otros_pagos": otros_pagos,
            "incapacidades": incapacidades
        }
        return res