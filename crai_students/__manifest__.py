{
    "name": "CRAI Students",
    "summary": "Modelo canónico de estudiantes para los módulos CRAI (desacoplado del origen)",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "author": "CRAI UMET",
    "depends": ["crai_base"],
    "data": [
        "security/ir.model.access.csv",
        #"security/rules.xml",
        "views/student_views.xml",
        "views/menu.xml",
        "views/res_config_settings_view.xml",  # <-- nuevo
        "data/cron.xml",
    ],
    "installable": True,
    "application": False,
}
