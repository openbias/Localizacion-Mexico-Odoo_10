# -*- coding: utf-8 -*-
{
    'name': "Validar Facturas",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",

    'category': 'Accounting & Finance',
    'version': '0.1.3',

    'depends': ['bias_base_report', 'cfd_mx', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        "views/account_invoice_view.xml",
        "wizard/validar_facturas_view.xml"
    ],
    'demo': [
    ],
}