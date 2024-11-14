from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentProfile(models.Model):
    _name = 'student_management.student_profile'
    _description = 'Perfil de Estudiante'
    _rec_name = 'name'

    barcode = fields.Char(string='Código de Barras', required=True,  unique=True, index=True)
    student_id = fields.Char(string='Cédula', required=True,  unique=True, index=True)
    name = fields.Char(string='Nombre Completo', required=True)
    email = fields.Char(string='Correo Electrónico', required=False)
    campus_id = fields.Many2one('student_management.campus', string='Sede', required=True)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', required=True)
    career_id = fields.Many2one('student_management.career', string='Carrera', required=True)
    has_disability = fields.Boolean(string='¿Tiene Discapacidad?', required=True)
    disability_type_id = fields.Many2one('student_management.disability_type', string='Tipo de Discapacidad')
    active = fields.Boolean(string='Activo', default=True)

    @api.constrains('barcode', 'student_id')
    def _check_unique_fields(self):
        for record in self:
            if self.search([('barcode', '=', record.barcode), ('id', '!=', record.id)]):
                raise ValidationError('El código de barras debe ser único.')
            if self.search([('student_id', '=', record.student_id), ('id', '!=', record.id)]):
                raise ValidationError('El ID del estudiante debe ser único.')

    @api.onchange('faculty_id')
    def _onchange_faculty_id(self):
        if self.faculty_id:
            return {'domain': {'career_id': [('faculty_id', '=', self.faculty_id.id)]}}
        else:
            return {'domain': {'career_id': []}}
