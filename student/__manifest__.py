{
    'name': 'Student Management',
    'version': '1.0',
    'summary': 'Gestion de los estudiantes Umet',
    'author': 'Elmer Rivadeneira',
    'depends': ['base', 'campus'],
    'data': [
        'security/security.xml',          # Roles y permisos
        'security/ir.model.access.csv',   # Acceso a modelos
        'views/student_view.xml',         # Vistas de estudiantes
	    'views/student_menu.xml',	#Menus del módulo
	    'views/library_access_views.xml',    #Vista  del modelo acceso  biblioteca
	    'views/library_access_action.xml',  #Accion del modelo acceso biblioteca
	    'views/library_access_menu.xml',    # Menu del modelo de acceso de biblioteva
    ],

    'assets': {
        'web.assets_backend': [
            'student/views/assets.xml',
        ],
    },

    'installable': True,
    'application': True,
}
