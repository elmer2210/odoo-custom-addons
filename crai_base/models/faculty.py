from odoo import fields, models

class CraiFaculty(models.Model):
    _name = "crai.faculty"
    _description = "Facultad"
    _order = "name"

    name = fields.Char("Nombre de facultad", required=True, translate=False)
    code = fields.Char("Código", help="Código interno de la facultad", translate=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("crai_faculty_code_unique", "unique(code)", "El código de la facultad debe ser único."),
    ]
