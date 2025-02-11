# -*- coding: utf-8 -*-
{
    'name': "studnent_dashboard",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """Dashboard estadísticos sobre la biblioteca""",

    'author': "Universidad Metropolitana",
    'website': "https://umet.edu.ec/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Library',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'board'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/student_dashboard_views.xml',
        'views/student_dashboard_menus.xml',
        'views/student_dashboard_board.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
    'installable': True,
    'application': True,
    'auto_install': False,
}

