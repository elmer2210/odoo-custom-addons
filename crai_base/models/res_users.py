from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    crai_campus_ids = fields.One2many(
        "crai.campus", "user_id", string="Sedes CRAI (responsable)"
    )
