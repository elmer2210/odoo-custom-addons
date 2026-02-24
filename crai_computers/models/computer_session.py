# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class CraiComputerSession(models.Model):
    _name = "crai.computer.session"
    _description = "CRAI Computer Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_at desc, id desc"

    state = fields.Selection([
        ("open", "Abierta"),
        ("closed", "Cerrada"),
        ("timeout", "Cerrada por inactividad"),
    ], default="open", index=True, tracking=True, required=True)

    computer_id = fields.Many2one("crai.computer", required=True, index=True, tracking=True, ondelete="restrict")
    student_id = fields.Many2one("crai.student", required=True, index=True, tracking=True, ondelete="restrict")
    
    # Campos relacionados para búsquedas rápidas
    number_id = fields.Char(related="student_id.number_id", store=True, index=True)
    email = fields.Char(related="student_id.email", store=True)
    student_name = fields.Char(related="student_id.name", store=True)
    computer_name = fields.Char(related="computer_id.name", store=True, index=True)

    computer_campus_id = fields.Many2one(
        "crai.campus", 
        string="Campus del Equipo", 
        related="computer_id.campus_id", 
        store=True, 
        index=True
    )

    site_id = fields.Many2one("crai.site", string="Sede", index=True)
    campus_id = fields.Many2one("crai.campus", string="Campus Estudiante", index=True)

    start_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True, tracking=True)
    end_at = fields.Datetime(index=True, tracking=True)
    duration_minutes = fields.Integer(compute="_compute_duration", store=True, string="Duración (min)")

    last_seen = fields.Datetime(
        string="Último latido",
        default=fields.Datetime.now,  # IMPORTANTE: inicializar con la fecha actual
        index=True,
        tracking=True
    )
    
    user_id = fields.Many2one("res.users", string="Registrado por", default=lambda s: s.env.user, readonly=True)
    source = fields.Selection([
        ("desktop_app", "App Escritorio"),
        ("kiosk", "Kiosk"),
        ("manual", "Manual"),
    ], default="kiosk", string="Origen", index=True)
    
    note = fields.Text()
    
    # Relación opcional con el registro de acceso
    reading_access_id = fields.Many2one("crai.reading.access", string="Registro de entrada", index=True)

    # ==================== CONSTRAINTS ====================
    @api.constrains("student_id", "state")
    def _check_single_open_per_student(self):
        """Un estudiante solo puede tener una sesión abierta a la vez"""
        for rec in self:
            if rec.state == "open":
                count = self.search_count([
                    ("student_id", "=", rec.student_id.id),
                    ("state", "=", "open"),
                    ("id", "!=", rec.id)
                ])
                if count:
                    raise ValidationError(
                        _("El estudiante %s ya tiene una sesión abierta.") % rec.student_id.name
                    )

    @api.constrains("computer_id", "state")
    def _check_single_open_per_computer(self):
        """Un equipo solo puede tener una sesión abierta a la vez"""
        for rec in self:
            if rec.state == "open":
                count = self.search_count([
                    ("computer_id", "=", rec.computer_id.id),
                    ("state", "=", "open"),
                    ("id", "!=", rec.id)
                ])
                if count:
                    raise ValidationError(
                        _("El equipo %s ya tiene una sesión abierta.") % rec.computer_id.name
                    )

    @api.constrains("start_at", "end_at")
    def _check_dates(self):
        """La fecha de fin debe ser posterior a la de inicio"""
        for rec in self:
            if rec.end_at and rec.start_at and rec.end_at < rec.start_at:
                raise ValidationError(_("La fecha de fin no puede ser anterior a la fecha de inicio."))

    # ==================== COMPUTED FIELDS ====================
    @api.depends("start_at", "end_at")
    def _compute_duration(self):
        for rec in self:
            if rec.end_at and rec.start_at:
                delta = rec.end_at - rec.start_at
                rec.duration_minutes = int(delta.total_seconds() // 60)
            else:
                rec.duration_minutes = 0

    # ==================== CRUD OVERRIDES ====================
    @api.model_create_multi
    def create(self, vals_list):
        """Al crear, asegurar que last_seen esté inicializado"""
        for vals in vals_list:
            if not vals.get("last_seen"):
                vals["last_seen"] = fields.Datetime.now()
        return super().create(vals_list)

    # ==================== API MÉTODOS (JSON-RPC desde App Escritorio) ====================
    @api.model
    def api_start_session(self, computer_code, number_id, email=None):
        """
        Inicia sesión desde app de escritorio vía JSON-RPC (execute_kw).
        
        Args:
            computer_code: Código único del equipo
            number_id: Cédula del estudiante
            email: (opcional) Email para validación adicional
        
        Returns:
            dict con session_id, start_at, computer, student
        """
        Computer = self.env["crai.computer"].sudo()
        Student = self.env["crai.student"].sudo()

        # Validar equipo
        comp = Computer.search([
            ("code", "=", (computer_code or "").strip()),
            ("is_active", "=", True)
        ], limit=1)
        if not comp:
            raise UserError(_("Equipo '%s' no encontrado o inactivo.") % computer_code)

        # Validar estudiante
        stu = Student.search([("number_id", "=", (number_id or "").strip())], limit=1)
        if not stu:
            raise UserError(_("Estudiante con cédula '%s' no encontrado.") % number_id)

        # Validar email (opcional)
        if email and stu.email:
            if email.strip().lower() != (stu.email or "").strip().lower():
                raise UserError(_("El correo no coincide con el estudiante."))

        # Verificar que no haya sesiones abiertas
        if self.search_count([("computer_id", "=", comp.id), ("state", "=", "open")]):
            raise UserError(_("El equipo '%s' ya tiene una sesión abierta.") % comp.name)
        
        if self.search_count([("student_id", "=", stu.id), ("state", "=", "open")]):
            raise UserError(_("El estudiante '%s' ya tiene una sesión abierta.") % stu.name)

        # Crear sesión
        now = fields.Datetime.now()
        vals = {
            "computer_id": comp.id,
            "student_id": stu.id,
            "site_id": stu.site_id.id if stu.site_id else False,
            "campus_id": stu.campus_id.id if stu.campus_id else False,
            "source": "desktop_app",
            "start_at": now,
            "last_seen": now,
        }
        rec = self.create(vals)
        
        return {
            "session_id": rec.id,
            "start_at": str(rec.start_at),
            "computer": comp.name,
            "student": stu.name,
            "message": _("Sesión iniciada correctamente."),
        }

    @api.model
    def api_heartbeat(self, session_id):
        """
        Actualiza 'last_seen' para mantener sesión activa.
        Debe llamarse periódicamente desde la app (ej. cada 60s).
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            bool True si se actualizó correctamente
        """
        rec = self.browse(int(session_id))
        if not rec.exists():
            raise UserError(_("Sesión no encontrada."))
        
        if rec.state != "open":
            raise UserError(_("La sesión ya está cerrada."))
        
        rec.write({"last_seen": fields.Datetime.now()})
        return True

    @api.model
    def api_finish_session(self, session_id):
        """
        Cierra sesión manualmente (usuario cierra la app).
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            dict con duration_minutes
        """
        rec = self.browse(int(session_id))
        if not rec.exists():
            raise UserError(_("Sesión no encontrada."))
        
        if rec.state != "open":
            raise UserError(_("La sesión ya está cerrada."))
        
        now = fields.Datetime.now()
        rec.write({
            "end_at": now,
            "state": "closed",
            "last_seen": now,
        })
        
        return {
            "duration_minutes": rec.duration_minutes,
            "message": _("Sesión cerrada correctamente."),
        }

    # ==================== MÉTODOS INTERNOS (desde Kiosk) ====================
    @api.model
    def assign_computer_to_student(self, student_id, campus_id, computer_id=None):
        """
        Asigna una computadora a un estudiante (desde kiosk).
        Si no se especifica computer_id, asigna una disponible automáticamente.
        
        Args:
            student_id: ID del estudiante
            campus_id: ID del campus
            computer_id: (opcional) ID del equipo específico
        
        Returns:
            dict con session_id, computer_name, message
        """
        Student = self.env["crai.student"].sudo()
        Computer = self.env["crai.computer"].sudo()

        # Validar estudiante
        student = Student.browse(student_id)
        if not student.exists():
            return {"ok": False, "message": _("Estudiante no encontrado.")}

        # Verificar si ya tiene sesión abierta
        if self.search_count([("student_id", "=", student_id), ("state", "=", "open")]):
            return {
                "ok": False,
                "message": _("El estudiante ya tiene una sesión abierta."),
            }

        # Si no se especifica equipo, buscar uno disponible
        if not computer_id:
            available = Computer.search([
                ("campus_id", "=", campus_id),
                ("is_active", "=", True),
            ])
            # Filtrar los que NO tienen sesión abierta
            for comp in available:
                if not self.search_count([("computer_id", "=", comp.id), ("state", "=", "open")]):
                    computer_id = comp.id
                    break

        if not computer_id:
            return {
                "ok": False,
                "message": _("No hay computadoras disponibles en este momento."),
            }

        # Validar que el equipo esté libre
        computer = Computer.browse(computer_id)
        if not computer.exists() or not computer.is_active:
            return {"ok": False, "message": _("Equipo no disponible.")}

        if self.search_count([("computer_id", "=", computer_id), ("state", "=", "open")]):
            return {"ok": False, "message": _("El equipo ya está ocupado.")}

        # Crear sesión
        now = fields.Datetime.now()
        vals = {
            "student_id": student_id,
            "computer_id": computer_id,
            "campus_id": campus_id,
            "site_id": student.site_id.id if student.site_id else False,
            "source": "kiosk",
            "start_at": now,
            "last_seen": now,
        }
        rec = self.create(vals)

        return {
            "ok": True,
            "session_id": rec.id,
            "computer_name": computer.name,
            "message": _("Computadora %s asignada correctamente.") % computer.name,
        }

    # ==================== CRON JOB ====================
    @api.model
    def _cron_close_idle_sessions(self):
        """
        Cierra automáticamente las sesiones inactivas.
        Ejecutado por cron cada N minutos.
        """
        IrConfig = self.env["ir.config_parameter"].sudo()
        timeout_minutes = int(IrConfig.get_param("crai_computers.session_timeout_minutes", 120))
        
        if timeout_minutes <= 0:
            return True  # Deshabilitado

        # Calcular límite de tiempo
        limit_dt = fields.Datetime.now() - timedelta(minutes=timeout_minutes)
        
        # Buscar sesiones abiertas sin heartbeat reciente
        idle_sessions = self.search([
            ("state", "=", "open"),
            ("last_seen", "!=", False),
            ("last_seen", "<", limit_dt)
        ])

        # Cerrar por timeout
        for session in idle_sessions:
            session.write({
                "end_at": fields.Datetime.now(),
                "state": "timeout",
            })
            # Opcional: notificar al estudiante
            session.message_post(
                body=_("Sesión cerrada automáticamente por inactividad (%s min).") % timeout_minutes
            )

        return True

    # ==================== ACCIONES DE BOTÓN ====================
    def action_close_session(self):
        """Botón para cerrar sesión manualmente desde interfaz"""
        self.ensure_one()
        if self.state != "open":
            raise UserError(_("La sesión ya está cerrada."))
        
        self.write({
            "end_at": fields.Datetime.now(),
            "state": "closed",
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sesión cerrada"),
                "message": _("La sesión se ha cerrado correctamente."),
                "type": "success",
            }
        }

    def action_reopen_session(self):
        """Botón para reabrir sesión (solo admin)"""
        self.ensure_one()
        if self.state == "open":
            raise UserError(_("La sesión ya está abierta."))
        
        # Verificar que no haya conflictos
        if self.search_count([("computer_id", "=", self.computer_id.id), ("state", "=", "open")]):
            raise UserError(_("El equipo ya tiene una sesión abierta."))
        
        if self.search_count([("student_id", "=", self.student_id.id), ("state", "=", "open")]):
            raise UserError(_("El estudiante ya tiene una sesión abierta."))
        
        self.write({
            "state": "open",
            "end_at": False,
            "last_seen": fields.Datetime.now(),
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sesión reabierta"),
                "message": _("La sesión se ha reabierto correctamente."),
                "type": "success",
            }
        }
