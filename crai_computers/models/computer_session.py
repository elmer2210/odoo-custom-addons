# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class CraiComputerSession(models.Model):
    _name = "crai.computer.session"
    _description = "CRAI Computer Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_at desc, id desc"

    state = fields.Selection([
        ("open", "Abierta"),
        ("closed", "Cerrada"),
        ("timeout", "Cerrada por inactividad"),
    ], default="open", index=True, tracking=True)

    computer_id = fields.Many2one("crai.computer", required=True, index=True, tracking=True)
    student_id = fields.Many2one("crai.student", required=True, index=True, tracking=True)
    number_id = fields.Char(related="student_id.number_id", store=False)
    email = fields.Char(related="student_id.email", store=False)

    site_id = fields.Many2one("crai.site", string="Sede", index=True)
    campus_id = fields.Many2one("crai.campus", string="Campus", index=True)

    start_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True, tracking=True)
    end_at = fields.Datetime(index=True, tracking=True)
    duration_minutes = fields.Integer(compute="_compute_duration", store=True)

    last_seen = fields.Datetime(string="Último latido", index=True, tracking=True)
    user_id = fields.Many2one("res.users", string="Registrado por", default=lambda s: s.env.user, readonly=True)

    note = fields.Text()

    @api.constrains("student_id", "state")
    def _check_single_open_per_student(self):
        for rec in self:
            if rec.state == "open":
                count = self.search_count([("student_id", "=", rec.student_id.id),
                                        ("state", "=", "open"),
                                        ("id", "!=", rec.id)])
                if count:
                    raise ValidationError(_("El estudiante ya tiene una sesión abierta."))

    @api.constrains("computer_id", "state")
    def _check_single_open_per_computer(self):
        for rec in self:
            if rec.state == "open":
                count = self.search_count([("computer_id", "=", rec.computer_id.id),
                                        ("state", "=", "open"),
                                        ("id", "!=", rec.id)])
                if count:
                    raise ValidationError(_("El equipo ya tiene una sesión abierta."))


    @api.depends("start_at", "end_at")
    def _compute_duration(self):
        for rec in self:
            if rec.end_at and rec.start_at:
                delta = fields.Datetime.to_datetime(rec.end_at) - fields.Datetime.to_datetime(rec.start_at)
                rec.duration_minutes = int(delta.total_seconds() // 60)
            else:
                rec.duration_minutes = 0

    # ---------- API (JSON-RPC): start / heartbeat / finish ----------
    @api.model
    def api_start_session(self, computer_code, number_id, email=None):
        """
        Inicia sesión desde app de escritorio vía JSON-RPC (execute_kw).
        Valida: equipo activo, estudiante existe, no hay sesión abierta del estudiante ni del equipo.
        """
        Computer = self.env["crai.computer"].sudo()
        Student = self.env["crai.student"].sudo()

        comp = Computer.search([("code", "=", (computer_code or "").strip()), ("is_active", "=", True)], limit=1)
        if not comp:
            raise UserError(_("Equipo no encontrado o inactivo."))

        stu = Student.search([("number_id", "=", (number_id or "").strip())], limit=1)
        if not stu:
            raise UserError(_("Estudiante no encontrado."))

        if email and stu.email and email.strip().lower() != (stu.email or "").strip().lower():
            raise UserError(_("Correo no coincide con el estudiante."))

        # Reglas: un open por computador y uno por estudiante
        if self.search_count([("computer_id", "=", comp.id), ("state", "=", "open")]):
            raise UserError(_("Este equipo ya tiene una sesión abierta."))
        if self.search_count([("student_id", "=", stu.id), ("state", "=", "open")]):
            raise UserError(_("El estudiante ya tiene una sesión abierta."))

        vals = {
            "computer_id": comp.id,
            "student_id": stu.id,
            "site_id": getattr(stu, "site_id", False) and stu.site_id.id or False,
            "campus_id": getattr(stu, "campus_id", False) and stu.campus_id.id or False,
            "last_seen": fields.Datetime.now(),
        }
        rec = self.create(vals)
        return {"session_id": rec.id, "start_at": rec.start_at, "computer": comp.name, "student": stu.name}

    @api.model
    def api_heartbeat(self, session_id):
        """
        Actualiza 'last_seen' para evitar timeout.
        Llamar periódicamente (ej. cada 60s) desde la app.
        """
        rec = self.browse(int(session_id))
        if not rec or rec.state != "open":
            raise UserError(_("Sesión no encontrada o ya cerrada."))
        rec.write({"last_seen": fields.Datetime.now()})
        return True

    @api.model
    def api_finish_session(self, session_id):
        """Cierra sesión (fin manual desde la app)."""
        rec = self.browse(int(session_id))
        if not rec or rec.state != "open":
            raise UserError(_("Sesión no encontrada o ya cerrada."))
        rec.write({"end_at": fields.Datetime.now(), "state": "closed"})
        return {"duration_minutes": rec.duration_minutes}

    @api.model
    def _cron_close_idle_sessions(self):
        IrConfig = self.env["ir.config_parameter"].sudo()
        minutes = int(IrConfig.get_param("crai_computers.session_timeout_minutes", 2))
        if minutes <= 0:
            return True
        limit_dt = fields.Datetime.subtract(fields.Datetime.now(), minutes=minutes)
        idle = self.search([("state", "=", "open"), ("last_seen", "!=", False), ("last_seen", "<", limit_dt)])
        # cerramos por inactividad
        for rec in idle:
            rec.write({"end_at": fields.Datetime.now(), "state": "timeout"})
        return True