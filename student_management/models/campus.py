from odoo import models, fields

class Campus(models.Model):
    _name = 'student_management.campus'
    _description = 'Campus'

    name = fields.Char(string='Nombre de la Sede', required=True)
    code = fields.Char(string='Código de la Sede', required=False)
    address = fields.Char(string='Dirección', required=False)
    description = fields.Text(string='Descripción', required=False)
    
    career_ids = fields.One2many('student_management.career', 'campus_id', string='Carreras')
