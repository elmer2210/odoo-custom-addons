{
    'name': 'Campus Management',
    'version': '1.0',
    'summary': 'Gestion de los campus UMET',
    'author': 'Elmer Rivadeneira',
    'category': 'Library',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/faculty_view.xml',
        'views/career_view.xml',
	'data/campus_data.xml',
	'data/faculty_data.xml',
        'data/career_data.xml',
    ],
    'installable': True,
    'application': True,
}
