from odoo import models, fields

class Career(models.Model):
    _name = 'student_management.career'
    _description = 'Carrera'

    name = fields.Char(string='Nombre de la Carrera', required=True)
    code = fields.Char(string='Código de la Carrera', required=False)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', required=True)
    description = fields.Text(string='Descripción', required=False)
