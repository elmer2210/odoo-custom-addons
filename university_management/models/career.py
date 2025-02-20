from odoo import models, fields

class Career(models.Model):
    _name = 'university.career'
    _description = 'Carrera'

    name = fields.Char(string='Nombre de la Carrera', required=True)
    code = fields.Char(string='Código de la Carrera', required=False)
    campus_id = fields.Many2one('university.campus', string='Sede', required=True)
    faculty_id = fields.Many2one('university.faculty', string='Facultad', required=True)
    description = fields.Text(string='Descripción', required=False)
