{
    'name': 'Gestión de Estudiantes',
    'version': '1.0',
    'summary': 'Gestión de perfiles de estudiantes para la biblioteca',
    'author': 'Tu Nombre o Empresa',
    'category': 'Education',
    'website': 'http://www.tu-sitio.com',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
          'views/menus.xml',
        'views/student_profile_views.xml',  # Cargar primero este archivo
        'views/campus_views.xml',
        'views/faculty_views.xml',
        'views/career_views.xml',
        'views/disability_type_views.xml',
        'data/disability_type_data.xml',  # Opcional
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
