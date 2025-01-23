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
        """Cambia el estado a 'Aprobado' y genera el reporte."""
        for record in self:
            _logger.debug("Generando reporte para: %s", self.name)
            report_service = self.env.ref('library_donations.report_donation')
            _logger.debug("Servicio de reporte: %s", report_service)
            id=[record.id]
            pdf_content, _ = report_service._render_qweb_pdf(id)
            _logger.debug("Contenido del PDF generado: %s", pdf_content[:100]) 

            # Crear un adjunto
            attachment = self.env['ir.attachment'].create({
                'name': f"Certificado_{record.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'library.donation',
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })

            # Mensaje en el registro
            record.message_post(body="Certificado generado y adjuntado automáticamente.",
                                attachment_ids=[attachment.id])

            # Cambiar estado a "Aprobado"
            record.state = 'approved'

    def _generate_donation_report(self):
        """Genera un PDF de prueba con un reporte QWeb registrado."""
        
        _logger.debug("Iniciando la generación del PDF de prueba para la donación: %s", self.name)

        # Obtener el servicio del reporte
        report_service = self.env.ref('library_donations.report_donation')

        _logger.debug("Servicio del reporte encontrado: %s", report_service)

        # Generar el contenido del reporte
        pdf = report_service._render_qweb_pdf(self.ids)
        pdf_binary = base64.b64encode(pdf[0])

        # Guardar el PDF generado en el registro
        # save pdf as attachment
        name = "My Attachment"
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': pdf_binary,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })