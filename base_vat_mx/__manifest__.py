# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Validación del RFC México',
    'version' : '1.0',
    'summary': 'Factura Electronica Mexico',
    'sequence': 30,
    'description': """
Validación del RFC de México
==================================

Validación del RFC de México para los partners.
(3 o 4 letras + 6 digitos + 3 carateres homoclave)

    """,
    'category' : 'Accounting & Finance',
    'website': 'http://bias.com.mx/',
    'images' : [],
    'author': 'OpenBIAS',
    'depends' : ['base_vat'],
    'data': [
        'base_vat_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: