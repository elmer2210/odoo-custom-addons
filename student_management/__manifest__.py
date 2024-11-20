{
    'name': 'Gestión de Estudiantes',
    'version': '1.0',
    'summary': 'Gestión de perfiles de estudiantes para la biblioteca',
    'author': 'Elmer Rivadeneira',
    'category': 'Education',
    'website': 'http://www.umet.edu.ec',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # Primero, cargar las vistas
        'views/student_profile_views.xml',
        'views/campus_views.xml',
        'views/faculty_views.xml',
        'views/career_views.xml',
        'views/disability_type_views.xml',
        # Luego, cargar las acciones
        'views/actions.xml',
        # Finalmente, cargar los menús
        'views/menus.xml',
        # Datos adicionales
        'data/report_paperformat.xml',  # Opcional
        'report/student_card_report.xml',  # Report definition
        'report/student_card_template.xml',  # Report template
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
