# -*- coding: utf-8 -*-
{
    "name": "CRAI - Reading Access",
    "version": "17.0.1.0.0",
    "summary": "Registro de ingresos/salidas a sala de lectura por escaneo de cédula",
    "category": "Library/CRAI",
    "author": "UMET CRAI",
    "license": "LGPL-3",
    "depends": ["crai_base", "crai_students"],
    "data": [
        "security/ir.model.access.csv",
        #"security/rules.xml",
        "views/menu.xml",
        "views/reading_access_views.xml",
        "views/res_config_settings_view.xml",
    ],
    "application": False,
    "installable": True,
}
