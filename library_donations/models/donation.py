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

    student_id = fields.Many2one('student_management.student_profile', string="Estudiante", required=True)

    donor_name = fields.Many2one('student_management.student_profile', string="Donante", readonly=True)
    campus_name = fields.Many2one('student_management.campus', string="Sede", readonly=True)
    career_name = fields.Many2one('student_management.career', string="Carrera", readonly=True)
    group_students = fields.One2many('student_management.student_profile', 'id', string="Estudiantes del Grupo")  # Relación para donaciones grupales
    donation_items = fields.One2many('library.donation.item', 'donation_id', string="Ítems Donados")  # Relación con los ítems donados
    total_cost = fields.Float(string="Costo Total", compute="_compute_total_cost", store=True)  # Costo total de los ítems
    invoice = fields.Binary(string="Factura (PDF)", required=True)
    invoice_name = fields.Char(string="Nombre de la Factura", required=True)
    details = fields.Text(string="Detalles de Factura", required=True)
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado'),
    ], string="Estado", default='requested', required=True)

    @api.depends('donation_items.cost')
    def _compute_total_cost(self):
        """Calcula el costo total de los ítems donados."""
        for record in self:
            record.total_cost = sum(item.cost for item in record.donation_items)

    @api.onchange('student_id', 'donation_type')
    def _onchange_student_id(self):
        """Valida la cédula para donación individual y rellena datos relacionados."""
        if self.donation_type == 'individual' and self.student_id:
            student = self.env['student_management.student_profile'].search([('student_id', '=', self.student_id)], limit=1)
            if student:
                self.donor_name = student.id
                self.campus_name = student.campus_id.id
                self.career_name = student.career_id.id
            else:
                self.donor_name = False
                self.campus_name = False
                self.career_name = False
                raise ValidationError("No se encontró un estudiante con la cédula ingresada.")
        elif self.donation_type == 'group':
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


class LibraryDonationItem(models.Model):
    _name = 'library.donation.item'
    _description = 'Ítem de Donación'

    title = fields.Char(string="Título", required=True)
    author = fields.Char(string="Autor", required=True)
    publication_year = fields.Char(string="Año de Publicación", required=True)
    cost = fields.Float(string="Costo", required=True)
    donation_id = fields.Many2one('library.donation', string="Donación", ondelete='cascade')
