from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryDonation(models.Model):
    _name = 'library.donation'
    _inherit = 'notification.mixin'
    _description = 'Gestión de Donaciones'

    # Campos
    donation_type = fields.Selection([
        ('individual', 'Individual'),
        ('group', 'Grupal')
    ], string="Tipo de Donación", required=True, default='individual')

    donor_name = fields.Many2one('student_management.student_profile', string="Donante", readonly=True)
    student_id = fields.Char(string="Cédula del Estudiante", required=False)  # Solo requerido para donaciones individuales
    campus_name = fields.Many2one('student_management.campus', string="Sede", readonly=True)
    career_name = fields.Many2one('student_management.career', string="Carrera", readonly=True)
    group_students = fields.One2many('student_management.student_profile', 'id', string="Estudiantes del Grupo")  # Relación para donaciones grupales
    invoice = fields.Binary(string="Factura (PDF)", required=True)
    invoice_name = fields.Char(string="Nombre de la Factura", required=True)
    details = fields.Text(string="Detalles de Factura", required=True)
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='requested', required=True)

    @api.onchange('student_id', 'donation_type')
    def _onchange_student_id(self):
        """Valida la cédula para donación individual y rellena datos relacionados."""
        if self.donation_type == 'individual' and self.student_id:
            # Buscar al estudiante por cédula
            student = self.env['student_management.student_profile'].search([('student_id', '=', self.student_id)], limit=1)
            if student:
                # Rellenar los campos relacionados
                self.donor_name = student.id
                self.campus_name = student.campus_id.id
                self.career_name = student.career_id.id
            else:
                # Limpiar los campos si no se encuentra el estudiante
                self.donor_name = False
                self.campus_name = False
                self.career_name = False
                raise ValidationError("No se encontró un estudiante con la cédula ingresada.")
        elif self.donation_type == 'group':
            # Limpiar campos individuales si es grupal
            self.student_id = False
            self.donor_name = False
            self.campus_name = False
            self.career_name = False

    @api.constrains('student_id', 'group_students', 'donation_type')
    def _check_donation_type(self):
        """Validación para asegurar que los datos estén completos según el tipo de donación."""
        for record in self:
            if record.donation_type == 'individual':
                if not record.student_id:
                    raise ValidationError("Debe ingresar la cédula de un estudiante para una donación individual.")
                student = self.env['student_management.student_profile'].search([('student_id', '=', record.student_id)], limit=1)
                if not student:
                    raise ValidationError("La cédula ingresada no corresponde a un estudiante válido.")
            elif record.donation_type == 'group':
                if not record.group_students:
                    raise ValidationError("Debe vincular al menos un estudiante para una donación grupal.")

    def action_review(self):
        for record in self:
            record.state = 'reviewed'

    def action_approve(self):
        for record in self:
            record.state = 'approved'
            record.send_notification(
                title="Donación Aprobada",
                message="La donación ha sido aprobada con éxito.",
                sticky=True,
                msg_type='success'
            )
