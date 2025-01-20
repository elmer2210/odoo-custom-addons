from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)


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

    # Reporte
    donation_report = fields.Binary(string="Reporte de Donación (PDF)", readonly=True)
    donation_report_name = fields.Char(string="Nombre del Reporte")

    # Estado
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string="Estado", default='requested', tracking=True)

    @api.model
    def create(self, vals):
        """Generar automáticamente el código de donación."""
        if 'name' not in vals or not vals['name']:
            campus = self.env['student_management.campus'].browse(vals['campus_id'])
            career = self.env['student_management.career'].browse(vals['career_id'])
            donation_type = vals.get('donation_type', 'individual')
            seq = self.env['ir.sequence'].next_by_code('library.donation') or '0000'
            vals['name'] = f"{donation_type[:3].upper()}-{campus.name[:3].upper()}-{career.name[:3].upper()}-{seq}"
        return super(LibraryDonation, self).create(vals)
    
    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if self.search([('name', '=', record.name), ('id', '!=', record.id)]):
                raise ValidationError(f"El código de donación '{record.name}' ya existe.")

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
            record._generate_donation_report()

    def _generate_donation_report(self):
        """Genera el reporte PDF y lo adjunta al registro."""
        try:
            _logger.debug("Iniciando generación del reporte para donación: %s", self.name)
            report_service = self.env.ref('library_donations.report_donation')

            if not report_service:
                raise UserError("El servicio del reporte no está configurado correctamente.")

            pdf_content, _ = report_service._render_qweb_pdf(self.ids)
            _logger.debug("PDF generado con éxito.")

            pdf_binary = base64.b64encode(pdf_content)
            self.write({
                'donation_report': pdf_binary,
                'donation_report_name': f"Certificado_Donación_{self.name}.pdf",
            })

        except Exception as e:
            _logger.error("Error al generar el reporte: %s", str(e))
            raise UserError(f"Error al generar el reporte: {str(e)}")
