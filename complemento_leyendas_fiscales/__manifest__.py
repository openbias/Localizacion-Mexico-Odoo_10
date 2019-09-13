# -*- coding: utf-8 -*-
{
    'name': "Complemento Leyendas Fiscales",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "OpenBias",
    'website': "http://www.bias.com.mx",
    'category': 'Accounting & Finance',
    'version': '0.1',
    'depends': ['cfd_mx', 'bias_base_report'],
    'data': [
         'security/ir.model.access.csv',
        'views/views.xml',
    ],
}