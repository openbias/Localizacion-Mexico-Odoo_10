# -*- coding: utf-8 -*-
{
    'name': "Complemento Pagos CFDI 3.3",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",

    'category': 'Accounting & Finance',
    'version': '10.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'account', 
        'base',
        'bias_base_report',
    ],

    # always loaded
    'data': [
        'views/account_payment_view.xml',
        'views/account_move_view.xml'

        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}