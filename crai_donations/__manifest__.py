# -*- coding: utf-8 -*-
{
    "name": "CRAI - Donaciones de Libros",
    "version": "17.0.1.0.0",
    "summary": "Gestión de donaciones de libros individuales, grupales y externas",
    "category": "Library/CRAI",
    "author": "UMET CRAI",
    "license": "LGPL-3",
    "depends": ["crai_base", "crai_students", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/sequence.xml",
        "data/mail_template.xml",
        "views/menu.xml",
        "views/donation_views.xml",
        "views/res_config_settings_view.xml",
        "report/donation_certificate_report.xml",
        "report/donation_certificate_template.xml",
    ],
    "application": False,
    "installable": True,
}
