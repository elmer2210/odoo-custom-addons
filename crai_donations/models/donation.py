# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import hashlib
import random
import string


class CraiDonation(models.Model):
    _name = "crai.donation"
    _description = "Donación de Libros"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "display_name"

    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    
    name = fields.Char(
        string="Número de Solicitud",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nuevo"),
        tracking=True
    )
    
    display_name = fields.Char(
        string="Nombre para Mostrar",
        compute="_compute_display_name",
        store=True
    )
    
    donation_type = fields.Selection(
        [
            ("individual", "Donación Individual"),
            ("group", "Donación Grupal"),
            ("external", "Donación Externa")
        ],
        string="Tipo de Donación",
        required=True,
        default="individual",
        tracking=True
    )
    
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("submitted", "Enviada"),
            ("approved", "Aprobada"),
            ("rejected", "Rechazada"),
            ("certificate_issued", "Certificado Emitido")
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
        copy=False
    )
    user_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    
    # ===============================
    # INFORMACIÓN DEL SOLICITANTE
    # ===============================
    
    # Para donaciones de estudiantes (individual o grupal)
    student_id = fields.Many2one(
        "crai.student",
        string="Estudiante Solicitante",
        index=True,
        tracking=True,
        help="Estudiante que realiza la solicitud (individual) o líder del grupo"
    )
    
    student_career_id = fields.Many2one(
        "crai.career",
        string="Carrera del Estudiante",
        related="student_id.career_id",
        store=True,
        readonly=True
    )
    
    # Para donaciones grupales - estudiantes adicionales
    group_student_ids = fields.Many2many(
        "crai.student",
        "crai_donation_student_rel",
        "donation_id",
        "student_id",
        string="Estudiantes del Grupo",
        domain="[('career_id', '=', student_career_id)]",
        help="Estudiantes adicionales que participan en la donación grupal (misma carrera)"
    )
    
    # Para donaciones externas
    external_donor_name = fields.Char(
        string="Nombre del Donante Externo",
        tracking=True
    )
    
    external_donor_email = fields.Char(
        string="Correo Electrónico",
        tracking=True
    )
    
    external_donor_phone = fields.Char(
        string="Teléfono",
        tracking=True
    )
    
    external_donor_organization = fields.Char(
        string="Organización",
        tracking=True
    )
    
    # ===============================
    # INFORMACIÓN DE LA DONACIÓN
    # ===============================
    
    campus_id = fields.Many2one(
        "crai.campus",
        string="Campus de Entrega",
        required=True,
        index=True,
        tracking=True,
        default=lambda self: self._default_campus()
    )
    
    book_ids = fields.One2many(
        "crai.donation.book",
        "donation_id",
        string="Libros Donados",
        copy=True
    )
    
    book_count = fields.Integer(
        string="Cantidad de Libros",
        compute="_compute_book_count",
        store=True
    )
    
    total_cost = fields.Float(
        string="Costo Total",
        compute="_compute_total_cost",
        store=True,
        tracking=True
    )
    
    invoice_file = fields.Binary(
        string="Factura Escaneada",
        attachment=True,
        help="Adjuntar factura de compra (requerido para donaciones de estudiantes)"
    )
    
    invoice_filename = fields.Char(
        string="Nombre del Archivo"
    )
    
    notes = fields.Text(
        string="Observaciones"
    )
    
    # ===============================
    # CAMPOS DE CONTROL Y AUDITORÍA
    # ===============================
    
    librarian_id = fields.Many2one(
        "res.users",
        string="Bibliotecario",
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )
    
    approver_id = fields.Many2one(
        "res.users",
        string="Aprobador",
        readonly=True,
        tracking=True
    )
    
    approval_date = fields.Datetime(
        string="Fecha de Aprobación",
        readonly=True,
        tracking=True
    )
    
    rejection_reason = fields.Text(
        string="Motivo de Rechazo",
        tracking=True
    )
    
    submission_date = fields.Datetime(
        string="Fecha de Envío",
        readonly=True,
        tracking=True
    )
    
    # ===============================
    # CERTIFICADO
    # ===============================
    
    certificate_number = fields.Char(
        string="Número de Certificado",
        readonly=True,
        copy=False,
        tracking=True
    )
    
    certificate_code = fields.Char(
        string="Código de Verificación",
        readonly=True,
        copy=False,
        help="Código único para validar autenticidad del certificado"
    )
    
    certificate_issued_date = fields.Datetime(
        string="Fecha de Emisión del Certificado",
        readonly=True
    )
    
    # ===============================
    # COMPUTED FIELDS
    # ===============================
    
    @api.depends("name", "donation_type", "student_id", "external_donor_name")
    def _compute_display_name(self):
        """Genera nombre descriptivo para mostrar"""
        for record in self:
            if record.name and record.name != _("Nuevo"):
                parts = [record.name]
                if record.donation_type == "external" and record.external_donor_name:
                    parts.append(f"- {record.external_donor_name}")
                elif record.student_id:
                    parts.append(f"- {record.student_id.name}")
                record.display_name = " ".join(parts)
            else:
                record.display_name = _("Donación Nueva")
    
    @api.depends("book_ids")
    def _compute_book_count(self):
        """Cuenta total de libros"""
        for record in self:
            record.book_count = len(record.book_ids)
    
    @api.depends("book_ids.cost")
    def _compute_total_cost(self):
        """Calcula costo total de todos los libros"""
        for record in self:
            record.total_cost = sum(record.book_ids.mapped("cost"))
    
    # ===============================
    # DEFAULTS Y HELPERS
    # ===============================
    
    @api.model
    def _default_campus(self):
        """Campus por defecto del usuario actual"""
        user = self.env.user
        campuses = user.sudo().crai_campus_ids
        return campuses[0].id if len(campuses) == 1 else False
    
    # ===============================
    # CONSTRAINTS Y VALIDACIONES
    # ===============================
    
    @api.constrains("donation_type", "student_id", "external_donor_name")
    def _check_donor_information(self):
        """Valida que se proporcione información del donante según el tipo"""
        for record in self:
            if record.donation_type in ("individual", "group") and not record.student_id:
                raise ValidationError(
                    _("Debe seleccionar un estudiante para donaciones individuales o grupales.")
                )
            if record.donation_type == "external" and not record.external_donor_name:
                raise ValidationError(
                    _("Debe ingresar el nombre del donante para donaciones externas.")
                )
    
    @api.constrains("donation_type", "group_student_ids")
    def _check_group_students(self):
        """Valida que las donaciones grupales tengan más estudiantes"""
        for record in self:
            if record.donation_type == "group" and len(record.group_student_ids) < 1:
                raise ValidationError(
                    _("Las donaciones grupales deben incluir al menos 2 estudiantes (solicitante + grupo).")
                )
    
    @api.constrains("donation_type", "invoice_file", "state")
    def _check_invoice_required(self):
        """Valida que las donaciones de estudiantes tengan factura antes de aprobar"""
        for record in self:
            if (
                record.state in ("approved", "certificate_issued")
                and record.donation_type in ("individual", "group")
                and not record.invoice_file
            ):
                raise ValidationError(
                    _("Las donaciones de estudiantes requieren adjuntar la factura antes de ser aprobadas.")
                )
    
    @api.constrains("book_ids")
    def _check_has_books(self):
        """Valida que haya al menos un libro"""
        for record in self:
            if record.state in ("submitted", "approved", "certificate_issued") and not record.book_ids:
                raise ValidationError(
                    _("Debe agregar al menos un libro a la donación.")
                )
    
    # ===============================
    # ONCHANGE METHODS
    # ===============================
    
    @api.onchange("donation_type")
    def _onchange_donation_type(self):
        """Limpia campos no relevantes al cambiar tipo"""
        if self.donation_type == "external":
            self.student_id = False
            self.group_student_ids = [(5, 0, 0)]
        else:
            self.external_donor_name = False
            self.external_donor_email = False
            self.external_donor_phone = False
            self.external_donor_organization = False
    
    @api.onchange("student_id")
    def _onchange_student_id(self):
        """Limpia grupo si cambia estudiante principal"""
        if self.student_id and self.group_student_ids:
            # Filtrar estudiantes que no sean de la misma carrera
            valid_students = self.group_student_ids.filtered(
                lambda s: s.career_id == self.student_id.career_id
            )
            if len(valid_students) != len(self.group_student_ids):
                self.group_student_ids = [(6, 0, valid_students.ids)]
    
    # ===============================
    # CRUD OVERRIDES
    # ===============================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Genera número de secuencia al crear"""
        for vals in vals_list:
            if vals.get("name", _("Nuevo")) == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code("crai.donation") or _("Nuevo")
        return super().create(vals_list)
    
    def unlink(self):
        """Previene borrado de donaciones aprobadas o con certificado"""
        for record in self:
            if record.state in ("approved", "certificate_issued"):
                raise UserError(
                    _("No puede eliminar donaciones aprobadas o con certificado emitido.")
                )
        return super().unlink()
    
    # ===============================
    # WORKFLOW METHODS
    # ===============================
    
    def action_submit(self):
        """Envía la solicitud para aprobación"""
        self.ensure_one()
        # Validaciones
        if not self.book_ids:
            raise UserError(_("Debe agregar al menos un libro antes de enviar."))
        
        if self.donation_type in ("individual", "group") and not self.invoice_file:
            raise UserError(_("Debe adjuntar la factura antes de enviar la solicitud."))
        
        self.write({
            "state": "submitted",
            "submission_date": fields.Datetime.now()
        })
        
        # Enviar notificación al aprobador
        self._send_submission_notification()
        
        self.message_post(
            body=_("Solicitud enviada para aprobación."),
            subject=_("Donación Enviada")
        )
    
    def action_approve(self):
        """Aprueba la donación (solo para grupo de aprobadores)"""
        self.ensure_one()
        
        # Verificar permisos
        if not self.env.user.has_group("crai_base.group_crai_donation_approver"):
            raise UserError(
                _("Solo los usuarios autorizados pueden aprobar donaciones.")
            )
        
        self.write({
            "state": "approved",
            "approver_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
            "rejection_reason": False
        })
        
        # Enviar notificación al donante
        self._send_approval_notification()
        
        self.message_post(
            body=_("Donación aprobada por %s") % self.env.user.name,
            subject=_("Donación Aprobada")
        )
    
    def action_reject(self):
        """Abre wizard para rechazar con motivo"""
        self.ensure_one()
        
        # Verificar permisos
        if not self.env.user.has_group("crai_base.group_crai_donation_approver"):
            raise UserError(
                _("Solo los usuarios autorizados pueden rechazar donaciones.")
            )
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "crai.donation.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_donation_id": self.id}
        }
    
    def action_set_to_draft(self):
        """Vuelve a borrador (solo si no está aprobada)"""
        for record in self:
            if record.state == "certificate_issued":
                raise UserError(
                    _("No puede volver a borrador una donación con certificado emitido.")
                )
            record.state = "draft"
    
    def action_generate_certificate(self):
        """Genera el certificado de donación con código único"""
        self.ensure_one()
        
        if self.state != "approved":
            raise UserError(
                _("Solo puede generar certificados para donaciones aprobadas.")
            )
        
        if self.certificate_number:
            raise UserError(
                _("Esta donación ya tiene un certificado emitido.")
            )
        
        # Generar número de certificado
        certificate_number = self.env["ir.sequence"].next_by_code("crai.donation.certificate")
        
        # Generar código de verificación único
        verification_code = self._generate_verification_code()
        
        self.write({
            "certificate_number": certificate_number,
            "certificate_code": verification_code,
            "certificate_issued_date": fields.Datetime.now(),
            "state": "certificate_issued"
        })
        
        # Enviar certificado por email
        self._send_certificate_notification()
        
        self.message_post(
            body=_("Certificado generado: %s") % certificate_number,
            subject=_("Certificado de Donación")
        )
        
        # Retornar acción para imprimir certificado
        return self.action_print_certificate()
    
    def action_print_certificate(self):
        """Imprime el certificado de donación"""
        self.ensure_one()
        
        if not self.certificate_number:
            raise UserError(
                _("Debe generar el certificado antes de imprimirlo.")
            )
        
        return self.env.ref("crai_donations.action_report_donation_certificate").report_action(self)
    
    # ===============================
    # MÉTODOS AUXILIARES
    # ===============================
    
    def _generate_verification_code(self):
        """Genera código único de verificación para el certificado"""
        # Combinar datos únicos de la donación
        unique_string = f"{self.id}{self.name}{fields.Datetime.now()}{random.randint(1000, 9999)}"
        
        # Generar hash SHA256
        hash_object = hashlib.sha256(unique_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Tomar primeros 16 caracteres y formatear
        code = hash_hex[:16].upper()
        # Formatear como XXXX-XXXX-XXXX-XXXX
        formatted_code = "-".join([code[i:i+4] for i in range(0, 16, 4)])
        
        return formatted_code
    
    # ===============================
    # NOTIFICACIONES POR EMAIL
    # ===============================
    
    def _send_submission_notification(self):
        """Notifica al aprobador sobre nueva solicitud"""
        self.ensure_one()
        
        template = self.env.ref("crai_donations.email_template_donation_submitted", raise_if_not_found=False)
        if not template:
            return
        
        # Obtener usuarios aprobadores
        approvers = self.env.ref("crai_base.group_crai_donation_approver").users
        
        for approver in approvers:
            template.with_context(approver_name=approver.name).send_mail(
                self.id,
                email_values={"email_to": approver.email},
                force_send=True
            )
    
    def _send_approval_notification(self):
        """Notifica al donante sobre aprobación"""
        self.ensure_one()
        
        template = self.env.ref("crai_donations.email_template_donation_approved", raise_if_not_found=False)
        if not template:
            return
        
        recipient_email = self.get_donor_email()
        if recipient_email:
            template.send_mail(
                self.id,
                email_values={"email_to": recipient_email},
                force_send=True
            )
    
    def _send_rejection_notification(self):
        """Notifica al donante sobre rechazo"""
        self.ensure_one()
        
        template = self.env.ref("crai_donations.email_template_donation_rejected", raise_if_not_found=False)
        if not template:
            return
        
        recipient_email = self._get_donor_email()
        if recipient_email:
            template.send_mail(
                self.id,
                email_values={"email_to": recipient_email},
                force_send=True
            )
    
    def _send_certificate_notification(self):
        """Envía certificado por email al donante"""
        self.ensure_one()
        
        template = self.env.ref("crai_donations.email_template_certificate_issued", raise_if_not_found=False)
        if not template:
            return
        
        recipient_email = self.get_donor_email()
        if recipient_email:
            template.send_mail(
                self.id,
                email_values={"email_to": recipient_email},
                force_send=True
            )
    
    def get_donor_email(self):  # <-- Le quitamos el guion bajo inicial
        """Obtiene email del donante, integrantes del grupo y secretaría de la sede"""
        self.ensure_one()
        emails = []
        
        # 1. Correos de los donantes/estudiantes
        if self.donation_type in ("individual", "group"):
            if self.student_id.email:
                emails.append(self.student_id.email)
            
            # Si es grupal, incluimos a todos los integrantes
            if self.donation_type == "group":
                emails.extend(self.group_student_ids.mapped('email'))
                
        elif self.donation_type == "external":
            if self.external_donor_email:
                emails.append(self.external_donor_email)
        
        # 2. Correo de secretaría configurado en la SEDE (Site)
        if self.campus_id and self.campus_id.site_id and self.campus_id.site_id.secretary_email:
            emails.append(self.campus_id.site_id.secretary_email)
                
        # Limpiamos valores vacíos y devolvemos la lista separada por comas
        return ",".join(list(set(filter(None, emails))))

# ===============================
# WIZARD DE RECHAZO
# ===============================

class CraiDonationRejectWizard(models.TransientModel):
    _name = "crai.donation.reject.wizard"
    _description = "Asistente para Rechazar Donación"
    
    donation_id = fields.Many2one(
        "crai.donation",
        string="Donación",
        required=True,
        readonly=True
    )
    
    rejection_reason = fields.Text(
        string="Motivo del Rechazo",
        required=True,
        help="Explique claramente por qué se rechaza la donación"
    )
    
    def action_confirm_reject(self):
        """Confirma el rechazo con el motivo proporcionado"""
        self.ensure_one()
        
        self.donation_id.write({
            "state": "rejected",
            "approver_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
            "rejection_reason": self.rejection_reason
        })
        
        # Enviar notificación
        self.donation_id._send_rejection_notification()
        
        self.donation_id.message_post(
            body=_("Donación rechazada por %s. Motivo: %s") % (
                self.env.user.name,
                self.rejection_reason
            ),
            subject=_("Donación Rechazada")
        )
        
        return {"type": "ir.actions.act_window_close"}
