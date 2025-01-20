# -*- coding: utf-8 -*-
{
     'name': 'Library Donations',
    'version': '1.0',
    'summary': 'Gestión de Donaciones para la Biblioteca',
    'description': """
        Permite gestionar las donaciones realizadas a la biblioteca, incluyendo 
        solicitudes, revisiones, aprobaciones y generación de certificados.
    """,
    'author': 'Sebas Inc.',
    'website': 'http://www.example.com',
    'category': 'Library',
    'depends': ['base', 'website', 'portal', 'student_management'],
    'data': [
        #'security/security.xml',
        'report/report_donation.xml',
        'report/report_donation_template.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/donation_views.xml',
        'views/donation_menu.xml',
    ],
    'installable': True,
    'application': True,
}

