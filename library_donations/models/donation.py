from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryDonation(models.Model):
    _name = 'library.donation'
    _description = 'Gestión de Donaciones'
    _inherit = ['mail.thread']

    name = fields.Char(string="Código de Donación", readonly=True, copy=False)
    donation_type = fields.Selection([
        ('individual', 'Individual'),
        ('group', 'Grupal')
    ], string="Tipo de Donación", required=True, default='individual')
    date = fields.Date(string="Fecha de Donación", default=fields.Date.context_today)

    # Clasificadores
    campus_id = fields.Many2one('student_management.campus', string="Sede", required=True)
    career_id = fields.Many2one(
        'student_management.career',
        string="Carrera",
        required=True,
        domain="[('faculty_id', '=', campus_id)]"
    )

    # Relación con estudiantes
    donor_ids = fields.Many2many(
        'student_management.student_profile',
        string="Donadores",
        domain="[('campus_id', '=', campus_id), ('career_id', '=', career_id)]"
    )

    # Ítems Donados
    donation_items = fields.One2many('library.donation.item', 'donation_id', string="Ítems Donados")
    total_cost = fields.Float(string="Costo Total", compute="_compute_total_cost", store=True)

    # Factura
    invoice_pdf = fields.Binary(string="Archivo de Factura (PDF)")
    invoice_number = fields.Char(string="Número de Factura", required=True)
    invoice_date = fields.Date(string="Fecha de Emisión", required=True)

    # Estado
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string="Estado", default='requested', tracking=True)

    @api.depends('donation_items.cost')
    def _compute_total_cost(self):
        """Calcula el costo total de los ítems donados."""
        for record in self:
            record.total_cost = sum(item.cost for item in record.donation_items)

    @api.constrains('invoice_number')
    def _check_invoice_number(self):
        """Asegura que el número de factura sea único."""
        for record in self:
            existing = self.search([('invoice_number', '=', record.invoice_number), ('id', '!=', record.id)])
            if existing:
                raise ValidationError(f"El número de factura '{record.invoice_number}' ya está registrado.")

    def action_review(self):
        """Cambiar el estado a 'Revisado'."""
        for record in self:
            record.state = 'reviewed'

    def action_approve(self):
        """Cambiar el estado a 'Aprobado'."""
        for record in self:
            record.state = 'approved'
