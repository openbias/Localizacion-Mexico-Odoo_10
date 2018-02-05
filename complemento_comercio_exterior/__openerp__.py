# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name' : 'Complemento Comercio Exterior',
    'version' : '1.0',
    'summary': 'Complemento Comercio Exterior',
    'sequence': 30,
    'description': """

    """,
    'category' : 'Accounting & Finance',
    'website': 'http://www.bias.com.mx',
    'images' : [],
    'author': 'OpenBIAS',
    'depends' : ['base', 'cfd_mx', 'account'],
    'data': [
        # 'ir.model.access.csv'
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: