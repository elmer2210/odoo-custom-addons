from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    campus_id = fields.Many2one('university.campus', string='Campus', help='El campus al que pertenece este usuario')
    is_donation_approver = fields.Boolean(string="Aprobador de Donaciones")