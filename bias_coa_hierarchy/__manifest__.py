# -*- coding: utf-8 -*-
{
    'name': "COA Hierarchy",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'bias_base_report'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_view.xml',
        'wizard/account_chart_view.xml',
        'report/report_accountchart_report_pdf.xml',
        'report/report_accountchartmoves_report_pdf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}