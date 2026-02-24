from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    crai_campus_ids = fields.Many2many(
        "crai.campus",
        relation="crai_campus_res_users_rel",
        column1="user_id_rel",
        column2="campus_id",
        string="Sedes CRAI (responsable)"
    )
