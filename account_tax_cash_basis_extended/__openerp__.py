# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Account Tax Cash Basis Extended',
    'version': '1.0',
    'category' : 'Accounting & Finance',
    'summary': 'This module add DIOT report, Fiscal Entries, and a buton in account entries to link payment, invoice and tax transfer entries',
    'description': """ 
Tax Model:
==========

- Create all the financial accounts for taxes: Accounting > Advicer > Chart of Accounts. 
- The module can handle up to 16 different taxes, but more can be added if needed, taxes already included are:
    * VAT 0% (IVA 0%)
    * VAT Exempt (IVA Excento)
    * VAT Exempt Importation (IVA Excento en Importaciones)
    * VAT 16% (IVA 16% en compras o ventas)
    * VAT 16% Importation (IVA 16% en compras o ventas usado en pedimentos)
    * VAT 16% Not Creditable (IVA no no acreditable)
    * Retention VAT 4% (Retencion de IVA 4% en fletes)
    * Retention VAT 10% (Retencion de IVA 10% en arrendamientos)
    * Retention VAT 10.67% (Retencion de IVA 10.67% en servicios profesionales)
    * Retention ISR 10% (Retencion de ISR 10% en servicios profesionales y arrendamientos)
    * IEPS (Impuesto especial sobre productos y servicios)
    * IEPS Importation (Impuesto especial sobre productos y servicios en importaciones)
- Creates all taxes using the respective fiscal accounts: Accounting > Configuration > Accounting > Taxes
- Go to Advanced Option tab to set the propper tag in Tags field.
- Every time that you reconcile a payment with an invoice, the model will create a fiscal entry in the Fiscal tab of payment entry.
- The fiscal entry contain taxes, bases, invoice, operation type and totals involved in transaction.
- If the payed invoice is in foreign corrency, the tax transfer will be done using the payed date rate.

Fiscal Entries:
==================

- The module add a new object "Fiscal Report Lines" that cantain all taxes involved in payment transaction, base and amount.
- Fiscal lines are created at the time to reconcile a payment with an invoice.
- Fiscal lines are show a new tab "Fiscal Lines" in bank or cash journal entries
- Fiscal lines can be used for tax calculation, the menu is in Accounting > Reporting > Generic Reporting > Taxes > Fiscal Lines
- The fiscal line types are:
    - Outcome.- when the bank account pay some document
    - Inter Bank Outcome.- when the bank account send money to other bank account.
    - Income.- when the bank account receives money to pay some document
    - Inter Bank Income.- when the bank account receives money from other bank account.

DIOT Report:
============

This module add a wizard to generate the external load file (batch type) for DIOT "DECLARACION INFORMATIVA DE OPERACIONES CON TERCEROS. SIMPLIFICADA” (Regla 5.1.13.),
This text file avoid the direct codify resulting in optimizing the time expended in presenting the duty to the SAT.
In order to work properly some aditionald field must be filled:
    * Supplier Type (Tipo de Tercero) in each supplier: Accounting > Supplier > Supplier > Accounting > Supplier Type
        - 04 - Proveedor Nacional
        - 05 - Proveedor Extranjero
        - 15- Proveedor global
    * Operation Type (Tipo de Operacion) in each supplier: Accounting > Supplier > Supplier > Accounting > Operation Type
        - 03 - Prestacion de Servicios Profesionales
        - 06 - Arrendamiento de Inmuebles
        - 85 – Otros
    * Fiscal ID (Numero de ID Fiscal) when supplier type is 05: ccounting > Supplier > Supplier > Accounting > Fiscal ID
    * The partner country is mandatory when the supplier is 05
    * And finally, configure all taxes.



To display all fiscal lines go to:
    * Accounting > Reporting > Tax Reports > Taxes > Fiscal Lines

To create the text file for external load go to:
    * Accounting > Reporting > Tax Reports > Taxes > DIOT Report
        - Select any date af the period.
        - Press button "Create DIOT File" and you can download the file "DIOT_YYYY-MM"

For more information contact info@bias.com.mx


""",
    'author': 'OpenBIAS',
    'depends': ['account_tax_cash_basis'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'views/partner_view.xml',
        'views/account_move_view.xml',
        'wizard/account_diot_view.xml',
        'views/account_menuitem.xml',
                   ],
    'website': 'http://www.bias.com.mx',
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
