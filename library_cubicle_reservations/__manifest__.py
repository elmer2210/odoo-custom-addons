{
    'name': 'Reservación de cubiculos de biblioteca',
    'version': '1.0',
    'category': 'Library',
    'summary': 'Manage library cubicle loans and reservations',
    'author': 'Elmer Rivadeneira',
    'depends': ['base', 'student_management', 'notif_utils'],
    'data': [
        'security/ir.model.access.csv',
        'views/library_cubicle_view.xml',
        'views/library_loan_view.xml',
        'views/library_reservation_view.xml',
        'views/res_users_view.xml',
        'views/library_kanban_view.xml',
        'views/actions.xml',
        'views/menus.xml',
        'data/cron_jobs.xml',  # Añadir esta línea
    ],
    'installable': True,
    'application': True,
}