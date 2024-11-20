{
    'name': 'Registro de Ingresos de Estudiantes',
    'version': '1.0',
    'summary': 'Registra los ingresos de estudiantes a la biblioteca mediante código de barras',
    'author': 'Elmer Rivadeneira',
    'category': 'Education',
    'website': 'http://www.umet.edu.ec',
    'depends': ['base', 'student_management','mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/student_entry_views.xml',
        'views/actions.xml',
        'views/menus.xml',
        #'views/assets.xml',  # Para cargar archivos JavaScript si es necesario
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
