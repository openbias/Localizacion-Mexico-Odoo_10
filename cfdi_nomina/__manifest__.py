# -*- coding: utf-8 -*-
{
    'name': "CFDI Nomina",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenBias",
    'website': "http://www.bias.com.mx",

    'category': 'Invoicing',
    'version': '0.1.2',

    # any module necessary for this one to work correctly
    'depends': [
        "base",
        'bias_base_report',
        'hr', 'hr_payroll', 
        'hr_payroll_account', 
        'hr_mx_ext', 'cfd_mx'
    ],

    # always loaded
    'data': [
        'data/cfdi_nomina.tipo.xml',
        'data/cfdi_nomina.regimen_contratacion.xml',
        'data/cfdi_nomina.riesgo_puesto.xml',
        'data/cfdi_nomina.origen_recurso.xml',
        'data/cfdi_nomina.periodicidad_pago.xml',
        'data/cfdi_nomina.tipo_horas.xml',
        'data/hr.contract.type.xml',
        "data/cfdi_nomina.codigo_agrupador.xml",

        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/cfdi_nomina_view.xml',
        'views/cfdi_nomina_hr_view.xml',        
        'views/hr_payslip_line_view.xml',
        
        # 'wizard/batch_cfdi_view.xml',
        'wizard/reporte_acumulado_view.xml',

        'report/report_menu_xml.xml',
        'report/hr_payslip_mx.xml'
    ],
}