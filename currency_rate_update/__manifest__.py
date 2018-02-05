# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Currency Rate Update",
    "version": "2.1",
    'summary': 'Currency Rate Update',
    'sequence': 100,
    'description': """
Tipo de cambio para solventar obligaciones denominadas en dólares de los EE.UU.A., pagaderas en la República Mexicana.
------------------------------------------------------
    """,
    "author": "OpenBIAS S.A.",
    "website": "www.bias.com.mx",
    "category": "Financial Management/Configuration",
    "depends": ['bias_base_report'],
    "data": [
        "data/service_cron_data.xml",
        "views/res_currency_view.xml",
        "wizard/currency_rate_wiz_views.xml"
    ],
    "demo": [],
    'external_dependencies': 
        {
            'python' : ['feedparser']
        },
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: