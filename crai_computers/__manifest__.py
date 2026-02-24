# -*- coding: utf-8 -*-
{
    "name": "CRAI Computers",
    "version": "17.0.1.0",
    "summary": "Uso de computadoras por estudiantes (sesiones y control)",
    "author": "UMET CRAI",
    "category": "Education",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/computer_views.xml",
        "views/computer_session_views.xml",
        "data/ir_cron.xml",
        "data/ir_config_parameter.xml",
    ],
    "installable": True,
    "application": False,
}
