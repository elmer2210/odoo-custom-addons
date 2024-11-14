from odoo import models, fields

class Faculty(models.Model):
    _name = 'student_management.faculty'
    _description = 'Facultad'

    name = fields.Char(string='Nombre de la Facultad', required=True)
    code = fields.Char(string='Código de la Facultad', required=False)
    campus_id = fields.Many2one('student_management.campus', string='Sede', required=True)
    description = fields.Text(string='Descripción', required=False)

    career_ids = fields.One2many('student_management.career', 'faculty_id', string='Carreras')
