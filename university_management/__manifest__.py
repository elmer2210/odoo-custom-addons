# -*- coding: utf-8 -*-
{
    'name': "Gestión Universidad",

    'summary': "Administración de la Universidad",

    'description': """
        Módulo encargado de la administración de sedes y carreras de la Universidad Metropolitana
    """,

    'author': "UMET",
    'website': "https://umet.edu.ec",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'University',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','notif_utils','university_groups_users'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #'security/library_rules.xml',
        'views/campus_views.xml',
        'views/career_views.xml',
        'views/faculty_views.xml',
        'views/res_users_view.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

