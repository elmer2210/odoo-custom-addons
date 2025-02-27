# -*- coding: utf-8 -*-
{
    'name': "library_donations",

    'summary': "Gestión de donaciones",

    'description': """
El presente módulo se encarga de gestionar las donaciones hechas a las biblioteca de la universidad UMET
    """,

    'author': "UMET",
    'website': "https://umet.edu.ec",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Library',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','notif_utils','university_groups_users','university_students'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/donation_views.xml',
        'data/donation_email_template.xml',
        'data/ir_sequence_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

