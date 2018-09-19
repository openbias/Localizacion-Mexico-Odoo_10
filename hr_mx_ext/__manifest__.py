# -*- coding: utf-8 -*-
{
    'name': "RH Mexico",
    'summary': """Campos adicionales para RRHH Mexico""",
    'description': """
        Campos adicionales para recursos humanos para Mexico como CURP, IMSS, Infonavit, etc
    """,
    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",
    'category': 'HR',
    'version': '0.2.0',
    'depends': [
        'base_setup',
        'hr', 
        'hr_recruitment', 
        'hr_payroll',
        'hr_contract'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_mx_ext.tipotrabajador.xml',
        'data/hr_mx_ext.tiposueldo.xml',
        'data/hr_mx_ext.tipojornada.xml',
        'data/hr_mx_ext.tipodescuento.xml',
        'data/hr_mx_ext.tipopensionados.xml',
        'data/hr_mx_ext.escolaridad.xml',
        'views/res_partner_view.xml',
        'views/views.xml',
        'views/hr_employee_view.xml',
        'views/hr_applicant_view.xml',
        'views/templates.xml',
    ],
}