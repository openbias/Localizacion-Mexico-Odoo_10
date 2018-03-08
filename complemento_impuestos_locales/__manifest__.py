# -*- coding: utf-8 -*-
{
    'name': "Complemento Impuestos Locales",
    'summary': """Complemento Impuestos Locales""",
    'description': """
        Complemento Impuestos Locales
    """,
    'sequence': 1009,
    'author': "OpenBIAS",
    'category' : 'Accounting & Finance',
    'website': 'http://www.bias.com.mx',
    'version': '1.0',
    'depends': ['base', 'cfd_mx', 'account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ]
}