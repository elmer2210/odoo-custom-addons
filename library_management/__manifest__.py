# -*- coding: utf-8 -*-
{
    'name': "Gestion Biblioteca",

    'summary': "Administración de procesos de la biblioteca",

    'description': """
  Módulo de administriación de las bibliotecas de la Universidad
    """,

    'author': "UMET",
    'website': "https://umet.edu.ec",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Library',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'university_management','university_students','university_groups_users','notif_utils', 'mail', 'library_donations'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #'security/library_rules.xml',
        'views/library_cubicle_views.xml',
        'views/library_loan_views.xml',
        'views/library_reservation_view.xml',
        'views/library_computer_views.xml',
        'views/library_entry_views.xml',
        'views/actions.xml',
        'views/menus.xml',
        'data/ir_cron.xml'
    ],
    # only loaded in demonstration mode

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

