from odoo import fields, models

class CraiCampus(models.Model):
    _name = "crai.site"
    _description = "Sede CRAI"
    _order = "name"

    name = fields.Char("Nombre de sede", required=True, translate=False)
    code = fields.Char("Código", required=True, help="Código corto de la sede", translate=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("crai_site_code_unique", "unique(code)", "El código de la sede debe ser único."),
    ]
