from odoo import fields, models

class CraiCareer(models.Model):
    _name = "crai.career"
    _description = "Carrera"
    _order = "name"

    name = fields.Char("Nombre de carrera", required=True, translate=False)
    code = fields.Char("Código", translate=False)
    faculty_id = fields.Many2one("crai.faculty", string="Facultad", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("crai_career_code_unique", "unique(code)", "El código de la carrera debe ser único."),
    ]
