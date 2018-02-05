# -*- coding: utf-8 -*-
{
    'name': "Complemento INE",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenBIAS",
    'website': "http://bias.com.mx/",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['cfd_mx', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
}