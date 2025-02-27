{
    'name': 'Notification Utilities',
    'version': '1.0',
    'summary': 'Utilidades para envío de notificaciones en Odoo',
    'author': 'Elmer Rivadeneira',
    'depends': [
        'base',
        'mail',
    ],  # Asegúrate de incluir el módulo 'bus'
    'data': [
        #'data/donation_email_template.xml',
    ],
    'installable': True,
    'application': False,
}
