# -*- coding: utf-8 -*-
{
    'name': "Complemento Pagos CFDI 3.3",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'sequence': 1006,
    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",
    'category': 'Accounting & Finance',
    'version': '10.0.0.2',
    'depends': [
        'base',
        'mail',
        'account', 
        'account_cancel',
        'bias_base_report',
        'cfd_mx'
    ],
    'data': [
        'views/account_view.xml',
        'views/complemento_pago_view.xml',
        'views/account_report_payment_receipt_templates.xml',
        'data/payment_receipt_data.xml',
    ]
}