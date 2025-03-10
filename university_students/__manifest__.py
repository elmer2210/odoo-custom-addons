# -*- coding: utf-8 -*-
{
    'name': "Gestión Estudiantes",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Administración de los perfiles de los estudiantes
    """,

    'author': "UMET",
    'website': "https://umet.edu.ec",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'University',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['university_management','notif_utils', 'university_groups_users','library_donations'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/student_profile_views.xml',
        'views/disability_type_views.xml',
        'views/actions.xml',
        'views/menus.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

