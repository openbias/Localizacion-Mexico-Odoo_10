# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Factura Electronica Mexico',
    'version' : '10.0.4.0.1',
    'summary': 'Factura Electronica Mexico 3.3',
    'sequence': 1000,
    'description': """
Factura Electronica Mexico 3.3
==================================

    """,
    'category' : 'Accounting & Finance',
    'website': 'http://bias.com.mx/',
    'images' : [],
    'author': 'OpenBIAS',
    'depends' : [
        'base',
        'bias_base_report',
        'account', 
        'sales_team'
    ],
    'data': [
        'security/cfd_mx_groups.xml',
        'security/ir.model.access.csv',
        'data/account_invoice.sql',
        
        "data/xml/account.tax.group.xml",
        "data/xml/res.bank.xml",
        "data/xml/cfd_mx.formapago.xml",
        "data/xml/cfd_mx.metodopago.xml",
        "data/xml/cfd_mx.regimen.xml",
        "data/xml/cfd_mx.usocfdi.xml",
        "data/xml/cfd_mx.aduana.xml",
        "data/xml/res.country.xml",
        "data/xml/cfd_mx.tiporelacion.xml",

        'views/cfd_mx_models_views.xml',
        'views/res_country_view.xml',
        'views/res_company_view.xml',
        'views/partner_view.xml',
        'views/account_view.xml',        
        'views/product_product_views.xml',
        'views/invoice_view.xml',
        'views/report_invoice_mx_document.xml',
        'views/report_supplierinvoice.xml',
        # 'data/mail.template.csv',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: