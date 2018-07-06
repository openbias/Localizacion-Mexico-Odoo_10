# -*- coding: utf-8 -*-
{
    'name': "BIAS Base Reports",

    'summary': """
        Base module to create xlsx report""",
    'author': 'OpenBIAS',
    'website': "http://bias.com.mx",
    'category': 'Reporting',
    'version': '10.0.2.0.2',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python': ['xlsxwriter']
    },
    'depends': [
        'sale', 'purchase', 'account', 'report'
    ],
    'data': [
        'data/report_data.xml',
        'report/report_menus.xml',
        'report/account_move.xml',
        'views/models_views.xml',
        'views/wiz_report_xlsx_view.xml'
    ],
    'installable': True,
}
