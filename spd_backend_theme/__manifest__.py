{
    "name" : "Backend theme in Odoo17",
    "version" : "17.0.0.1",
    "category" : "theme",
    'summary': 'Change backend colors',
    "description": """
    This module for changing backend colors
    """,
    "depends" : ['base'],
    'assets': {
        'web.assets_backend': [
            'spd_backend_theme/static/src/css/backend.css',
        ],
    },
    'qweb': [],
    'author': 'SPD Solutions Pvt. Ltd.',
    'company': 'SPD Solutions Pvt. Ltd.',
    'maintainer': 'SPD Solutions Pvt. Ltd.',
    "images": [
        "static/description/banner.png",
    ],
    'license':'LGPL-3',
    "auto_install": False,
    "installable": True,
}
