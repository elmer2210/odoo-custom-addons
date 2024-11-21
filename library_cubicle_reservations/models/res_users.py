from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    campus_id = fields.Many2one('student_management.campus', string='Campus', help='El campus al que pertenece este usuario')