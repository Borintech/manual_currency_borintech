# -*- coding: utf-8 -*-
{
    'name': "Custom rate",

    'summary': """
        take the custom rate for calculate amount other currency in account move lines and modify 
        l10n_ar_currency_rate with currency_rate 
        """,

    'description': """Modulo desarrollado exclusivamente para borintech srl, permite la modificación manual del tipo de cambio en facturas y notas de crédito
    """,

    'author': "Devman",

    'website': "http://www.devman.com.ar",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',

    'sequence': -2,

    'version': '4.2',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_latam_invoice_document',
        'l10n_latam_base',
        'account'
    ],
    # always loaded
    'data': [
        'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,

    'auto_install': False,

    'application': False,
}
