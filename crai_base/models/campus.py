from odoo import fields, models

class CraiCampus(models.Model):
    _name = "crai.campus"
    _description = "Campus CRAI"
    _order = "name"

    name = fields.Char("Nombre de Campus", required=True, translate=False)
    code = fields.Char("Código", required=True, help="Código corto de la sede", translate=False)
    site_id = fields.Many2one('crai.site', string="Sede", required=True, ondelete='restrict', index=True)
    user_id = fields.Many2one('res.users', string="Responsable", ondelete="set null", index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("crai_campus_code_unique", "unique(code)", "El código de la sede debe ser único."),
    ]
