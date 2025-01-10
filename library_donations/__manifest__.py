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
        'security/ir.model.access.csv',
        'views/donation_views.xml',
        'views/donation_menu.xml',
        'report/donation_certificate.xml',
    ],
    'installable': True,
    'application': True,
}

