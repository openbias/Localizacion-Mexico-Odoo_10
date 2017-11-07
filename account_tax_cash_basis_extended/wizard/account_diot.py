# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import UserError

import time
import calendar
from types import NoneType, StringType
import unicodedata
import base64
#import csv
from datetime import datetime
import math

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def remove_accents(s):
    def remove_accent1(c):
        return unicodedata.normalize('NFD', c)[0]
    return u''.join(map(remove_accent1, s))

QUERY_DIOT = """
SELECT
  p.name AS supplier,
/*
TODOS LOS CAMPOS DEBEN DE ESTAR EN UN SOLO RENGLON SEPARADOS POR EL CARACTER | (PIPE)
DENTRO DE UN ARCHIVO DE TIPO TEXTO (.txt)
 
EJEMPLO:
Campo1|Campo2|Campo3...|CampoN|
Campo1|Campo2|Campo3...|CampoN|
 
		ORDEN Y TIPO DE CAMPOS
*/
/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 INFORMACION DE IDENTIFICACION DEL PROVEEDOR O TERCERO     
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
*/

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Campo: 1
 Descripcion: 			Tipo de tercero
 Dato obligatorio 		
 Valores permitidos: 		
			Valor		Descripcion
			-------		--------------
			00		Seleccione...
			04		Proveedor Nacional 
			05		Proveedor Extranjero
			15		Proveedor Global
Longitud: 2 
*/
  p.supplier_type::varchar(2) AS campo_1,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 2
 Descripcion: 			Tipo de operacion
 Dato obligatorio 		
 Valores permitidos: 		
			Valor		Descripcion
			-------		--------------
			00		Seleccione...
			03		Prestacion de Servicios Profesionales
			06		Arrendamiento  de Inmuebles
			85		Otros
 
Cuando el tipo de tercero sea igual a: 05 solo aplicaran los valores 03 y 85
Longitud: 2
*/
  p.operation_type::varchar(2) AS campo_2,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 3
 Descripcion: 			Registro Federal de Contribuyentes
 Tipo de campo: 		RFC
 Personas fisicas y morales 	
 Homoclave requerida 		
 Dato opcional 		
 
Obligatorio cuando: tipo de tercero sea igual a: 04
Opcional cuando: tipo de tercero sea igual a: 05
No obligatorio cuando: tipo de tercero sea igual a: 15
Longitud: 13
*/
  --TRANSLATE(p.vat, '-. ', '')::varchar(13) AS campo_3,
  MAX(CASE WHEN p.supplier_type='05' THEN NULL ELSE TRANSLATE(p.vat, '-. ', '') END)::varchar(13) AS campo_3,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 4
 Descripcion: 			Numero de ID fiscal
 Tipo de campo: 		Alfanumerico
 Caracteres especiales:	CONSULTAR EN ./data/layout_diot.txt
 Dato opcional 		
 
Aplica solo cuando tipo de tercero sea igual a: 05
Longitud: 40
*/
  MAX(CASE WHEN p.supplier_type='05' THEN p.fiscal_id END)::varchar(40) AS campo_4,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 5
 Descripcion: 			Nombre del extranjero
 Tipo de campo: 		Alfanumerico
 Caracteres especiales:	CONSULTAR EN ./data/layout_diot.txt
 Dato opcional 		
 
Aplica solo cuando tipo de tercero sea igual a: 05
Longitud: 43
*/
  MAX(CASE WHEN p.supplier_type='05' THEN p.name END)::varchar(43) AS campo_5,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 6
 Descripcion: 			Pais de residencia
 Dato obligatorio 		
 Valores permitidos: 		
			Valor		Descripcion
			-------		--------------
			0		  
			AD		AD - Principado de Andorra
			AE		AE - Emiratos Arabes Unidos
			AF		AF - Afganistan
			AG		AG - Antigua y Bermuda
			AI		AI - Isla Anguilla
			AL		AL - Republica de Albania
			AN		AN - Antillas Neerlandesas
			AO		AO - Republica de Angola
			AQ		AQ - Antartica
			AR		AR - Argentina
			AS		AS - Samoa Americana
			AT		AT - Austria
			AU		AU - Australia
			AW		AW - Aruba
			AX		AX - Ascension
			AZ		AZ - Islas Azores
			BB		BB - Barbados
			BD		BD - Bangladesh
			BE		BE - Belgica
			BF		BF - Burkina Faso
			BG		BG - Bulgaria
			BH		BH - Estado de Bahrein
			BI		BI - Burundi
			BJ		BJ - Benin
			BL		BL - Belice
			BM		BM - Bermudas
			BN		BN - Brunei Darussalam
			BO		BO - Bolivia
			BR		BR - Brasil
			BS		BS - Commonwealth de las Bahamas
			BT		BT - Buthan
			BU		BU - Burma
			BV		BV - Isla Bouvet
			BW		BW - Botswana
			BY		BY - Bielorrusia
			CA		CA - Canada
			CC		CC - Isla de Cocos o Kelling
			CD		CD - Islas Canarias
			CE		CE - Isla de Christmas
			CF		CF - Republica Centro Africana
			CG		CG - Congo
			CH		CH - Suiza
			CI		CI - Costa de Marfil
			CK		CK - Islas Cook
			CL		CL - Chile
			CM		CM - Camerun
			CN		CN - China
			CO		CO - Colombia
			CP		CP - Campione D'Italia
			CR		CR - Republica de Costa Rica
			CS		CS - Republica Checa y Republica Eslovaca
			CU		CU - Cuba
			CV		CV - Republica de Cabo Verde
			CX		CX - Isla de Navidad
			CY		CY - Republica de Chipre
			DD		DD - Alemania
			DJ		DJ - Republica de Djibouti
			DK		DK - Dinamarca
			DM		DM - Republica Dominicana
			DN		DN - Commonwealth de Dominica
			DZ		DZ - Argelia
			EC		EC - Ecuador
			EG		EG - Egipto
			EH		EH - Sahara del Oeste
			EO		EO - Estado Independiente de Samoa Occidental
			ES		ES - España
			ET		ET - Etiopia
			FI		FI - Finlandia
			FJ		FJ - Fiji
			FK		FK - Islas Malvinas
			FM		FM - Micronesia
			FO		FO - Islas Faroe
			FR		FR - Francia
			GA		GA - Gabon
			GB		GB - Gran Bretaña (Reino Unido)
			GD		GD - Granada
			GF		GF - Guyana Francesa
			GH		GH - Ghana
			GI		GI - Gibraltar
			GJ		GJ - Groenlandia
			GM		GM - Gambia
			GN		GN - Guinea
			GP		GP - Guadalupe
			GQ		GQ - Guinea Ecuatorial
			GR		GR - Grecia
			GT		GT - Guatemala
			GU		GU - Guam
			GW		GW - Guinea Bissau
			GY		GY - Republica de Guyana
			GZ		GZ - Islas de Guernesey, Jersey, Alderney, Isla Great Sark, Herm, Little Sark, Berchou, Jethou, Lihou (Islas del Canal)
			HK		HK - Hong Kong
			HM		HM - Islas Heard and Mc Donald
			HN		HN - Republica de Honduras
			HT		HT - Haiti
			HU		HU - Hungria
			ID		ID - Indonesia
			IE		IE - Irlanda
			IH		IH - Isla del Hombre
			IL		IL - Israel
			IN		IN - India
			IO		IO - Territorio Britanico en el Oceano Indico
			IP		IP - Islas Pacifico
			IQ		IQ - Iraq
			IR		IR - Iran
			IS		IS - Islandia
			IT		IT - Italia
			JM		JM - Jamaica
			JO		JO - Reino Hachemita de Jordania
			JP		JP - Japon
			KE		KE - Kenia
			KH		KH - Campuchea Democratica
			KI		KI - Kiribati
			KM		KM - Comoros
			KN		KN - San Kitts
			KP		KP - Republica Democratica de Corea
			KR		KR - Republica de Corea
			KW		KW - Estado de Kuwait
			KY		KY - Islas Caiman
			LA		LA - Republica Democratica de Laos
			LB		LB - Libano
			LC		LC - Santa Lucia
			LI		LI - Principado de Liechtenstein
			LK		LK - Republica Socialista Democratica de Sri Lanka
			LN		LN - Labuan
			LR		LR - Republica de Liberia
			LS		LS - Lesotho
			LU		LU - Gran Ducado de Luxemburgo
			LY		LY - Libia
			MA		MA - Marruecos
			MC		MC - Principado de Monaco
			MD		MD - Madeira
			MG		MG - Madagascar
			MH		MH - Republica de las Islas Marshall
			ML		ML - Mali
			MN		MN - Mongolia
			MO		MO - Macao
			MP		MP - Islas Marianas del Noreste
			MQ		MQ - Martinica
			MR		MR - Mauritania
			MS		MS - Monserrat
			MT		MT - Malta
			MU		MU - Republica de Mauricio
			MV		MV - Republica de Maldivas
			MW		MW - Malawi
			MY		MY - Malasia 
			MZ		MZ - Mozambique
			NA		NA - Republica de Namibia
			NC		NC - Nueva Caledonia
			NE		NE - Niger
			NF		NF - Isla de Norfolk
			NG		NG - Nigeria
			NI		NI - Nicaragua
			NL		NL - Holanda
			NO		NO - Noruega
			NP		NP - Nepal
			NR		NR - Republica de Nauru
			NT		NT - Zona Neutral
			NU		NU - Niue
			NV		NV - Nevis
			NZ		NZ - Nueva Zelandia
			OM		OM - Sultania de Oman
			PA		PA - Republica de Panama
			PE		PE - Peru
			PF		PF - Polinesia Francesa
			PG		PG - Papua Nueva Guinea
			PH		PH - Filipinas
			PK		PK - Pakistan
			PL		PL - Polonia
			PM		PM - Isla de San Pedro y Miguelon
			PN		PN - Pitcairn
			PR		PR - Estado Libre Asociado de Puerto Rico
			PT		PT - Portugal
			PU		PU - Patau
			PW		PW - Palau
			PY		PY - Paraguay
			QA		QA - Estado de Quatar
			QB		QB - Isla Qeshm
			RE		RE - Reunion
			RO		RO - Rumania
			RW		RW - Rhuanda
			SA		SA - Arabia Saudita
			SB		SB - Islas Salomon
			SC		SC - Seychelles Islas
			SD		SD - Sudan
			SE		SE - Suecia
			SG		SG - Singapur
			SH		SH - Santa Elena
			SI		SI - Archipielago de Svalbard
			SJ		SJ - Islas Svalbard and Jan Mayen
			SK		SK - Sark
			SL		SL - Sierra Leona
			SM		SM - Serenisima Republica de San Marino
			SN		SN - Senegal
			SO		SO - Somalia
			SR		SR - Surinam
			ST		ST - Sao Tome and Principe
			SU		SU - Paises de la Ex-U.R.S.S., excepto Ucrania y Bielorusia
			SV		SV - El Salvador
			SW		SW - Republica de Seychelles
			SY		SY - Siria
			SZ		SZ - Reino de Swazilandia
			TC		TC - Islas Turcas y Caicos
			TD		TD - Chad
			TF		TF - Territorios Franceses del Sureste
			TG		TG - Togo
			TH		TH - Thailandia
			TK		TK - Tokelau
			TN		TN - Republica de Tunez
			TO		TO - Reino de Tonga
			TP		TP - Timor Este
			TR		TR - Trieste
			TS		TS - Tristan Da Cunha
			TT		TT - Republica de Trinidad y Tobago
			TU		TU - Turquia
			TV		TV - Tuvalu
			TW		TW - Taiwan
			TZ		TZ - Tanzania
			UA		UA - Ucrania
			UG		UG - Uganda
			UM		UM - Islas menores alejadas de los Estados Unidos
			US		US - Estados Unidos de America
			UY		UY - Republica Oriental del Uruguay
			VA		VA - El Vaticano
			VC		VC - San Vicente y Las Granadinas
			VE		VE - Venezuela
			VG		VG - Islas Virgenes Britanicas
			VI		VI - Islas Virgenes de Estados Unidos de America
			VN		VN - Vietnam
			VU		VU - Republica de Vanuatu
			WF		WF - Islas Wallis y Funtuna
			XX		XX - Otro
			YD		YD - Yemen Democratica
			YE		YE - Republica del Yemen
			YU		YU - Paises de la Ex-Yugoslavia
			ZA		ZA - Sudafrica
			ZC		ZC - Zona Especial Canaria
			ZM		ZM - Zambia
			ZO		ZO - Zona Libre Ostrava
			ZR		ZR - Zaire
			ZW		ZW - Zimbawe
 
Obligatorio solo cuando exista valor en el campo NOMBRE DEL EXTRANJERO
Longitud: 2
*/
  MAX(CASE WHEN c.code='MX' THEN NULL ELSE c.code END)::varchar(2) AS campo_6,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 7
 Descripcion: 			Nacionalidad
 Tipo de campo: 		Alfabetico
 Caracteres especiales:	CONSULTAR EN ./data/layout_diot.txt
 Dato opcional 		
 
Obligatorio solo cuando exista valor en el campo NOMBRE DEL EXTRANJERO
Longitud: 40
*/
  MAX(CASE WHEN c.code='MX' THEN NULL ELSE c.name END)::varchar(40) AS campo_7,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 INFORMACION DE IMPUESTO AL VALOR AGREGADO (IVA)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
tax_0   VAT 0
tax_1   VAT Exempt
tax_2   VAT Exempt Importation
tax_3   VAT 16
tax_4   VAT 16 Importation
tax_5   VAT 16 Not Creditable
tax_6   Retention VAT 4
tax_7   Retention VAT 10
tax_8   Retention VAT 10.67
tax_9   Retention ISR 10
tax_a   IEPS
tax_b   IEPS Importation
tax_c   
tax_d   
tax_e   
tax_f   
*/

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 8
 Descripcion: 			Valor de los actos o actividades pagados a la tasa del 15% o 16% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12 
*/
  NULLIF(
            TRUNC(
                    SUM(COALESCE(f.base_3,0)) 
                 )
      ,0)::varchar(12) AS campo_8,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 9
 Descripcion: 			Valor de los actos o actividades pagados a la tasa del 15% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodo Enero 2010
ESTE CAMPO SE UTILIZARa uNICAMENTE PARA EFECTOS DE DECLARAR ENAJENACIoN DE BIENES, PRESTACIoN DE SERVICIOS O EL OTORGAMIENTO DEL USO O GOCE TEMPORAL DE BIENES CELEBRADAS CON ANTERIORIDAD AL EJERCICIO 2010, ASi COMO DE CONFORMIDAD CON LO ESTABLECIDO EN LAS DISPOSICIONES TRANSITORIAS DE LA LEY DEL IMPUESTO AL VALOR AGREGADO.
*/
  NULL::varchar(12) AS campo_9,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 10
 Descripcion: 			Monto del IVA pagado no acreditable a la tasa del 15% o 16%  (correspondiente en la proporcion de las deducciones autorizadas)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 

EN LAS DEDUCCIONES PARCIALMENTE DEDUCIBLES SE INDICARa EL MONTO QUE NO SEA DEDUCIBLE PARA EFECTOS DEL ISR; EJEMPLO: EN UN GASTO DONDE EL 80% ES DEDUCIBLE Y EL 20% NO ES DEDUCIBLE, EL IVA QUE SE ANOTARa EN ESTE CAMPO ES EL QUE CORRESPONDA AL 20%
*/
  NULL::varchar(12) AS campo_10,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 11
 Descripcion: 			Valor de los actos o actividades pagados a la tasa del 10% u 11% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodos menor o igual a Enero 2014
*/
  NULL::varchar(12) AS campo_11,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 12
 Descripcion: 			Valor de los actos o actividades pagados a la tasa del 10% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodo Enero 2010
ESTE CAMPO SE UTILIZARa uNICAMENTE PARA EFECTOS DE DECLARAR ENAJENACIoN DE BIENES, PRESTACIoN DE SERVICIOS O EL OTORGAMIENTO DEL USO O GOCE TEMPORAL DE BIENES CELEBRADAS CON ANTERIORIDAD AL EJERCICIO 2010, ASi COMO DE CONFORMIDAD CON LO ESTABLECIDO EN LAS DISPOSICIONES TRANSITORIAS DE LA LEY DEL IMPUESTO AL VALOR AGREGADO.
*/
  NULL::varchar(12) AS campo_12,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 13
 Descripcion: 			Monto del IVA pagado no acreditable a la tasa del 10% u 11% (correspondiente en la proporcion de las deducciones autorizadas)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodos menor o igual a Enero 2014
EN LAS DEDUCCIONES PARCIALMENTE DEDUCIBLES SE INDICARa EL MONTO QUE NO SEA DEDUCIBLE PARA EFECTOS DEL ISR; EJEMPLO: EN UN GASTO DONDE EL 80% ES DEDUCIBLE Y EL 20% NO ES DEDUCIBLE, EL IVA QUE SE ANOTARa EN ESTE CAMPO ES EL QUE CORRESPONDA AL 20%
Longitud: 12 
*/
  NULL::varchar(12) AS campo_13,

/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 14
 Descripcion: 			Valor de los actos o actividades pagados en la importacion de bienes y servicios a la tasa del 15% o 16% de  IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12 
*/
  NULLIF(TRUNC(SUM(COALESCE(f.base_4,0))),0)::varchar(12) AS campo_14,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 15
 Descripcion: 			Monto del IVA pagado no acreditable por la importacion  a la tasa del 15% o 16% (correspondiente en la proporcion de las deducciones autorizadas)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 

EN LAS DEDUCCIONES PARCIALMENTE DEDUCIBLES SE INDICARa EL MONTO QUE NO SEA DEDUCIBLE PARA EFECTOS DEL ISR; EJEMPLO: EN UN GASTO DONDE EL 80% ES DEDUCIBLE Y EL 20% NO ES DEDUCIBLE, EL IVA QUE SE ANOTARa EN ESTE CAMPO ES EL QUE CORRESPONDA AL 20%
Longitud: 12 
*/
  NULLIF(TRUNC(
                ABS(SUM(COALESCE(f.tax_5,0)))
              )
      ,0)::varchar(12) AS campo_15,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 16
 Descripcion: 			Valor de los actos o actividades pagados en la importacion de bienes y servicios a la tasa del 10% u 11% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodos menor o igual a Enero 2014
EN LAS DEDUCCIONES PARCIALMENTE DEDUCIBLES SE INDICARa EL MONTO QUE NO SEA DEDUCIBLE PARA EFECTOS DEL ISR; EJEMPLO: EN UN GASTO DONDE EL 80% ES DEDUCIBLE Y EL 20% NO ES DEDUCIBLE, EL IVA QUE SE ANOTARa EN ESTE CAMPO ES EL QUE CORRESPONDA AL 20%
Longitud: 12 
*/
  NULL::varchar(12) AS campo_16,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 17
 Descripcion: 			Monto del IVA pagado no acreditable por la importacion a la tasa del 10% u 11% (correspondiente en la proporcion de las deducciones autorizadas)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
 
Aplica unicamente para periodos menor o igual a Enero 2014
EN LAS DEDUCCIONES PARCIALMENTE DEDUCIBLES SE INDICARa EL MONTO QUE NO SEA DEDUCIBLE PARA EFECTOS DEL ISR; EJEMPLO: EN UN GASTO DONDE EL 80% ES DEDUCIBLE Y EL 20% NO ES DEDUCIBLE, EL IVA QUE SE ANOTARa EN ESTE CAMPO ES EL QUE CORRESPONDA AL 20%
Longitud: 12 
*/
  NULL::varchar(12) AS campo_17,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 18
 Descripcion: 			Valor de los actos o actividades pagados en la importacion de bienes y servicios por los que no se paraga el IVA (Exentos)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12 
*/
  NULLIF(TRUNC(SUM(COALESCE(f.base_2,0))),0)::varchar(12) AS campo_18,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 19
 Descripcion: 			Valor de los demas actos o actividades pagados a la tasa del 0% de IVA
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12 
*/
  NULLIF(TRUNC(SUM(COALESCE(f.base_0,0))),0)::varchar(12) AS campo_19,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 20
 Descripcion: 			Valor de los actos o actividades pagados por los que no se pagara el IVA (Exentos)
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12 
*/
  NULLIF(TRUNC(SUM(COALESCE(f.base_1,0))),0)::varchar(12) AS campo_20,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 21
 Descripcion: 			IVA Retenido por el contribuyente
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
*/
  NULLIF(
            TRUNC(
                    ABS(SUM(COALESCE(f.tax_6,0)) + SUM(COALESCE(f.tax_7,0)) + SUM(COALESCE(f.tax_8,0)))
               ,0)
      ,0)::varchar(12) AS campo_21,


/*
------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 Campo: 22
 Descripcion: 			IVA correspondiente a las devoluciones, descuentos y bonificaciones sobre compras
 Tipo de campo: 		Numerico
 Valor minimo:  		0
 Valor maximo:  		999999999999
 Dato opcional 		
Longitud: 12
*/
  NULL::varchar(12) AS campo_22,

  NULL::varchar(12) AS fin



  
FROM
  account_move_fiscal f LEFT JOIN
  account_move m ON f.move_id = m.id LEFT JOIN
  res_partner p ON f.partner_id = p.id LEFT JOIN
  res_country c ON p.country_id = c.id 
"""

QUERY_WHERE = """
WHERE 
    m.company_id = %s AND
    f.operation_type = 'outcome' AND
    p.supplier = True AND
    m.date >= '%s' AND m.date <= '%s' 
"""

QUERY_GROUP = """
GROUP BY p.supplier_type, p.operation_type, p.vat, p.id ORDER BY p.supplier_type,p.vat,campo_5
"""

QUERY_DETAIL = """
            SELECT
              l.id AS line_id,
              p.vat,
              p.name AS partner_name,
              (CASE WHEN p.supplier_type='05' THEN p.name END)::varchar(43) AS campo_5
            FROM
              account_move m  LEFT JOIN
              account_move_line l ON l.move_id = m.id LEFT JOIN
              account_account a ON l.account_id = a.id LEFT JOIN
              account_account_type t ON a.user_type_id = t.id LEFT JOIN
              account_journal j ON m.journal_id = j.id LEFT JOIN
              res_partner p ON m.partner_id = p.id
            WHERE
              m.date >= '%s' AND m.date <= '%s' AND
              m.partner_id IS NOT NULL AND
              j.type = 'bank' AND
              t.type = 'payable'
            ORDER BY p.supplier_type,p.vat,campo_5,m.date
        """
class account_diot(models.TransientModel):
    _name = 'account.diot'
    _description = 'Account DIOT'

    company_id = fields.Many2one('res.company', string='Company', readonly=False, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Date')
    date_to = fields.Date(string='End Date')
    diot_file = fields.Binary(string='DIOT File', readonly=True)
    filename = fields.Char(string='File Name')
    state = fields.Selection([('choose', 'choose'),('get', 'get')], default='choose')        

    ###########################################################################################################################################
    #       CREATE DIOT FILE
    #{'currency_id': 34, u'tax_3': -155.18, u'tax_0': -0.0, u'base_4': 10350.0, u'tax_4': -1656.0, u'base_0': -10350.0, 'invoice_id': 1096, u'base_3': 969.83, 'payment_total': -2781.01, 'invoice_total': 2781.01}
    ###########################################################################################################################################
    @api.multi
    def create_detailed_diot_file(self):
        diot_report_format = ['vat', 'partner', 'invoice', 'invoice_tax',
                              'invoice_date', 'invoice_rate', 'invoice_amount', 'invoice_currency',
                              'payment_date', 'payment_rate', 'payment_amount', 'payment_currency', 
                              'payment_mxn', 'base_3', 'total']
        header = {'vat':'RFC', 'partner':'EMPRESA', 'invoice':'FACTURA', 'invoice_tax':'Impuestos en Factura',
                              'invoice_date':'FECHA FACTURA', 'invoice_rate':'TC FACTURA', 'invoice_amount':'MONTO FACTURA', 'invoice_currency':'MONEDA',
                              'payment_date':'FECHA DE PAGO', 'payment_rate':'TC PAGO', 'payment_amount':'MONTO DEL PAGO', 'payment_currency':'MONEDA', 
                              'payment_mxn':'MONTO EN PESOS', 'base_3':'BASE IVA 16%', 'total':'TOTAL DE RFC'}
        tag = {'tax_0':"IVA 0%",'tax_1':"IVA Excento",'tax_2':"IVA Excento en Importaciones",'tax_3':"IVA 16% en compras o ventas", 
               'tax_4':"IVA 16% en compras o ventas usado en pedimentos", 'tax_5':"IVA no no acreditable",'tax_6':"Retencion de IVA 4% en fletes",
               'tax_7':"Retencion de IVA 10% en arrendamientos", 'tax_8':"Retencion de IVA 10.67% en servicios profesionales", 
               'tax_9':"Retencion de ISR 10% en servicios profesionales y arrendamientos", 'tax_a':"Impuesto especial sobre productos y servicios", 
               'tax_b':"Impuesto especial sobre productos y servicios en importaciones", 'tax_c':"TAX c", 'tax_d':"TAX d", 'tax_e':"TAX e",'tax_f':"TAX f"}
        val = {}
        vat = [False,0]
        result = [header]

        self.date_from, self.date_to = self.get_month_day_range(self.date_from)
        query = QUERY_DETAIL%(self.date_from, self.date_to)
        self._cr.execute(query)
        for reg in self._cr.dictfetchall():
            payment_line = self.env['account.move.line'].browse(reg['line_id'])
            res = payment_line.get_base(operation_type='outcome')
            val = dict((k,'') for k in diot_report_format)
            val.update({
                    'payment_rate': payment_line.amount_currency and round((payment_line.debit-payment_line.credit)/payment_line.amount_currency, 4) or '',
                    'payment_date': payment_line.date,
                    'payment_mxn': payment_line.debit-payment_line.credit,
                    'payment_amount': payment_line.amount_currency or '',
                    'payment_currency': payment_line.currency_id.name,
                    'base_3': res.get('base_3',''),
                    'vat': reg.get('vat',''),
                    'partner': reg.get('partner_name',''),
                })
            if res.get('invoice_id'):
                invoice = self.env['account.invoice'].browse(res['invoice_id'])
                rate = round(invoice.move_id.amount/invoice.amount_total, 4)
                val.update({
                    'invoice': (invoice.reference and invoice.reference or '') + (invoice.number and ' ['+invoice.number+']' or ''),
                    'invoice_amount': invoice.amount_total,
                    'invoice_currency': invoice.currency_id.name,
                    'invoice_rate': (self.company_id.currency_id != invoice.currency_id) and rate or '', # TODO Enhance this rate calculation
                    'invoice_date':invoice.date_invoice,
                    'invoice_tax': ', '.join(map(str, [tag[x] for x in res if 'tax' in x])),
                    })
            if val.get('vat'):
                if val.get('vat','_') != vat[0]:
                    vat = [val['vat'],res.get('base_3',0)]
                else:
                    result[-1]['total'] = ''
                    vat[1] += res.get('base_3',0)
                val.update({'total':vat[1] and (math.floor(vat[1] * 10 ** 0) / 10 ** 0) or 0})
            result.append(val)
            file_name = 'GRID_' + self.date_from[:-3] + '.csv'
        return self.open_file(result, diot_report_format, file_name)

    @api.multi
    def create_diot_file(self):
        result = []
        self.date_from, self.date_to = self.get_month_day_range(self.date_from)
        query_where = QUERY_WHERE%(self.company_id.id, self.date_from, self.date_to)
        query = QUERY_DIOT + query_where + QUERY_GROUP 
        self._cr.execute(query)
        diot_report_format = [desc[0] for desc in self._cr.description]
        diot_report_format.pop(0)
        for reg in self._cr.dictfetchall():
            if reg['campo_1']=='04' and not reg['campo_3']:
                raise UserError(_('Warning!\n%s is defined as Supplier and "Proveedor Nacional" and does not have VAT')%reg['supplier'])
            reg.pop('supplier', None)
            result.append(reg)
        file_name = 'DIOT_' + self.date_from[:-3] + '.txt'
        return self.open_file(result, diot_report_format, file_name)

    @api.multi
    def open_file(self, result, diot_report_format, file_name):
        if not result:
            raise UserError(_('Warning!\nThe report have no result'))
        csv_data = []
        # Order Correction
        for reg in result:
            row = []
            for key in diot_report_format:
                row.append(reg[key])
            csv_data.append(row)
        self.diot_file = self.ouput_csv(csv_data)
        self.filename = file_name
        self.state = 'get'
        # Open DIOT Wizard
        module = 'account_tax_cash_basis_extended'
        action = 'action_account_diot'
        model, action_id = self.pool['ir.model.data'].get_object_reference(self._cr, self._uid, module, action)
        action = self.pool[model].read(self._cr, self._uid, action_id, context=self._context)
        action = self.pool[model].read(self._cr, self._uid, action_id)
        action.update({'res_id': self.id})
        return action

    @api.model
    def get_month_day_range(self, date):
        """
        For a date 'date' returns the start and end date for the month of 'date'.

        Month with 31 days:
        >>> date = datetime.date(2011, 7, 27)
        >>> get_month_day_range(date)
        (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

        Month with 28 days:
        >>> date = datetime.date(2011, 2, 15)
        >>> get_month_day_range(date)
        (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
        """
        d = datetime.strptime(date, '%Y-%m-%d')
        first_day = d.replace(day = 1)
        last_day = d.replace(day = calendar.monthrange(d.year, d.month)[1])
        return first_day, last_day

    @api.model
    def ouput_csv(self, csv_data):
        def process(d):
            if isinstance(d, unicode):
                d = remove_accents(d) # d = d.encode('utf-8')
            elif isinstance(d, (bool, NoneType)): 
                d = ''
            return d
        buf = StringIO()
        for datas in csv_data:
            row, first = '', False
            for d in datas:
                if isinstance(d, (unicode,str)):
                    d = ''.join(i for i in d if ord(i)<128)
                    row += (first and '|' or '') + process(d)
                else:
                    row += (first and '|' or '') + str(process(d))
                first = True
            buf.write(row+'\n')
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return out

account_diot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
