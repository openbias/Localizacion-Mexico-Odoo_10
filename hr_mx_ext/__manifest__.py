# -*- coding: utf-8 -*-
{
    'name': "RH Mexico",

    'summary': """Campos adicionales para RRHH Mexico""",

    'description': """
        Campos adicionales para recursos humanos para Mexico como CURP, IMSS, Infonavit, etc
    """,

    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base_setup',
        'hr', 
        'hr_recruitment', 
        'hr_payroll',
        'hr_contract'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/hr_mx_ext.tipotrabajador.xml',
        # 'data/hr_mx_ext.tiposueldo.xml',
        # 'data/hr_mx_ext.tipojornada.xml',
        'data/hr_mx_ext.tipodescuento.xml',
        'data/hr_mx_ext.tipopensionados.xml',
        'data/hr_mx_ext.escolaridad.xml',

        'views/views.xml',
        'views/hr_employee_view.xml',
        'views/hr_applicant_view.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}