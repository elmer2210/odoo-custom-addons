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
    attachment_id = fields.Many2one('ir.attachment', string="Certificado PDF", readonly=True)
    has_attachment = fields.Boolean(string="¿Tiene PDF?", compute="_compute_has_attachment", store=True)

    # Estado
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('requested', 'Solicitado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ], default='draft', string="Estado")

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

    def action_request(self):
        """Cambiar el estado a Solicitado."""
        for record in self:
            record.state = 'requested'

    def action_reject(self):
        """Cambiar el estado a Rechazado."""
        for record in self:
            record.state = 'rejected'
    
    def action_approve(self):
        """Cambia el estado a 'Aprobado' y genera el reporte."""

        nombre_archivo = f"Reporte-{self.name}.pdf"
        self.action_generate_certificate(nombre_archivo)
        

        # Cambiar estado a "Aprobado"
        self.state = 'approved'

    @api.depends('attachment_id')
    def _compute_has_attachment(self):
        """Controla si el certificado tiene un adjunto generado"""
        for record in self:
            record.has_attachment = bool(record.attachment_id)
    
    def action_generate_certificate(self, nombre_archivo):
        """Genera el PDF y lo adjunta al registro como archivo adjunto en Odoo"""
        self.ensure_one()  # Asegura que se ejecuta en un solo registro

        # Generar el PDF del reporte
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'library_donations.report_donation',  # External ID de la plantilla
            self.ids,  # IDs de los registros a generar el reporte
            data={'o': self}
        )
        #pdf_content = report[0]


        attachment = self.env['ir.attachment'].create({
            'name': nombre_archivo,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),  # Codificar el contenido en base64
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

          # Guardar el adjunto en el campo attachment_id
        self.attachment_id = attachment.id

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_download_certificate(self):
        """Permite descargar el PDF sin abrir el modelo de attachments"""
        self.ensure_one()
        
        if not self.attachment_id:
            raise UserError("No hay un certificado generado para este registro.")
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }