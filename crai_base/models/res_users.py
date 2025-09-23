from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    crai_campus_ids = fields.Many2many(
        "crai.campus",
        "res_users_crai_campus_rel",
        "user_id",
        "campus_id",
        string="Sedes CRAI asignadas",
        help="Sedes que el usuario puede gestionar/visualizar (bibliotecarios pueden tener varias sedes).",
    )
