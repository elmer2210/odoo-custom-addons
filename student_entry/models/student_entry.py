from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentEntry(models.Model):
    _name = 'student.entry'
    _description = 'Registro de Ingresos de Estudiantes'
    _order = 'entry_time desc'

    student_id = fields.Many2one(
        'student_management.student_profile',
        string='Estudiante',
        required=True,
        domain=[('active', '=', True)],
    )
    entry_time = fields.Datetime(string='Fecha y Hora de Ingreso', default=fields.Datetime.now, required=True)
    campus_id = fields.Many2one('student_management.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('student_management.career', string='Carrera', related='student_id.career_id', store=True)

    @api.model
    def create_entry(self, barcode):
        student = self.env['student_management.student_profile'].search([('barcode', '=', barcode)], limit=1)
        if student and student.active:
            entry = self.create({'student_id': student.id})
            return entry
        else:
            raise ValidationError('El estudiante con el código de barras proporcionado no existe o está inactivo.')

    def action_register_entry(self):
        self.ensure_one()
        self.entry_time = fields.Datetime.now()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
