# -*- coding: utf-8 -*-
{
    'name': "Contabilidad Electronica",
    'summary': """
        Obligación que tienen los contribuyentes de enviar mensualmente 
        por medios electrónicos parte de su información financiera 
        al Servicio de Administración Tributaria (SAT)""",
    'description': """
        La contabilidad electrónica se refiere a la obligación de llevar los registros y 
        asientos contables a través de medios electrónicos e ingresar de forma mensual 
        su información contable a través de la página de Internet del SAT.
    """,
    'sequence': 1002,
    'author': "OpenBIAS",
    'website': "http://www.bias.com.mx",
    'category': 'Accounting & Finance',
    'version': '1.0.3',
    'depends': [
        'base',
        'bias_base_report'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/contabilidad_electronica.naturaleza.xml',
        'data/contabilidad_electronica.metodo.pago.xml',
        'data/contabilidad_electronica.codigo.agrupador.xml',
        'views/account_account_view.xml',
        'views/account_payment_view.xml',
        'wizard/account_move_comprobantes_view.xml',
        "wizard/generar_xmls_view.xml"
    ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: