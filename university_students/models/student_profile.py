from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentProfile(models.Model):
    _name = 'student.profile'
    _description = 'Perfil de Estudiante'
    _rec_name = 'completename'

    barcode = fields.Char(string='Código de Barras', required=True,  unique=True, index=True)
    student_id = fields.Char(string='Cédula', required=True,  unique=True, index=True)
    names = fields.Char(string='Nombres Completo', required=True)
    lastnames = fields.Char(string='Aprellidos Completo', required=True)
    completename = fields.Char(string='Nombres y Apellidos',  compute='_compute_completename', store=True)
    email = fields.Char(string='Correo Electrónico', required=False)
    campus_id = fields.Many2one('university.campus', string='Sede', required=True)
    faculty_id = fields.Many2one('university.faculty', string='Facultad', required=True)
    career_id = fields.Many2one('university.career', string='Carrera', required=True)
    has_disability = fields.Boolean(string='¿Tiene Discapacidad?', required=True)
    disability_type_id = fields.Many2one('student.disability', string='Tipo de Discapacidad')
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
    
    @api.depends('names', 'lastnames')
    def _compute_completename(self):
        for record in self:
            names = filter(None, [record.names, record.lastnames])
            record.completename = " ".join(names)
