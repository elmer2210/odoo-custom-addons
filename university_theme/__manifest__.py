# -*- coding: utf-8 -*-
{
    'name': "Tema del Sistema UMET",

    'summary': "Tema personalizado para el sistema de UMET",

    'description': """
Tema personalizado para el sistema.
    """,

    'author': "UMET",
    'website': "https://umet.edu.ec",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Theme',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'views/layout.xml',
        'views/dashboard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'university_theme/static/src/js/dashboard.js',
            'university_theme/static/src/scss/style.scss',
        ],
    },
    'application': False,
    'license': 'LGPL-3',
}

