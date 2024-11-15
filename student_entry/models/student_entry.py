from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentEntry(models.Model):
    _name = 'student.entry'
    _description = 'Registro de Ingresos de Estudiantes'
    _order = 'entry_time desc'
    
    barcode = fields.Char(string='Código de Barras', required=True, help="Escanee el código de barras del estudiante")
    student_id = fields.Many2one(
        'student_management.student_profile',
        string='Estudiante',
        required=True,
        compute='_compute_student_from_barcode',
        store=True,
        domain=[('active', '=', True)],
    )
    entry_time = fields.Datetime(string='Fecha y Hora de Ingreso', default=fields.Datetime.now, required=True)
    campus_id = fields.Many2one('student_management.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('student_management.career', string='Carrera', related='student_id.career_id', store=True)

    @api.depends('barcode')
    def _compute_student_from_barcode(self):
        for record in self:
            if record.barcode:
                student = self.env['student_management.student_profile'].search([('barcode', '=', record.barcode)], limit=1)
                if student and student.active:
                    record.student_id = student
                else:
                    record.student_id = False

    @api.model
    def create(self, vals):
        # Validar el código de barras antes de crear el registro
        barcode = vals.get('barcode')
        if barcode:
            student = self.env['student_management.student_profile'].search([('barcode', '=', barcode)], limit=1)
            if not student or not student.active:
                raise ValidationError('El estudiante con el código de barras proporcionado no existe o está inactivo.')
            vals['student_id'] = student.id
        else:
            raise ValidationError('Debe proporcionar un código de barras válido.')

        return super(StudentEntry, self).create(vals)

    def action_register_entry(self):
        self.ensure_one()
        self.entry_time = fields.Datetime.now()
        self.message_post(body=f"Ingreso registrado para el estudiante {self.student_id.name} a las {self.entry_time}")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
