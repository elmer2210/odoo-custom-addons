# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re

class ReadingAccess(models.Model):
    _name = "crai.reading.access"
    _description = "Reading Room Access"
    _order = "occurred_at desc"
    _rec_name = "student_id"

    student_id = fields.Many2one(
        "crai.student", string="Estudiante", required=True, index=True, ondelete="restrict"
    )
    campus_id = fields.Many2one(
        "crai.campus", string="Biblioteca", required=True, index=True, ondelete="restrict",
        default=lambda self: self._default_campus()
    )
    student_home_campus_id = fields.Many2one(
        "crai.campus", string="Campus del estudiante",
        related="student_id.campus_id", store=True, index=True
    )
    # Solo entradas (IN): ya no existe access_type
    source = fields.Selection(
        [("kiosk", "Kiosk"), ("manual", "Manual"), ("api", "API")], string="Tipo de acceso",
        default=lambda self: self._default_source(), required=True, index=True
    )
    occurred_at = fields.Datetime(
        string="Hora Entrada", default=lambda self: fields.Datetime.now(), index=True
    )
    operator_id = fields.Many2one(
        "res.users", string="Bibliotecario", default=lambda self: self.env.user, readonly=True
    )
    notes = fields.Char()

    # Para filtros/estadísticas
    student_career_id = fields.Many2one(
        "crai.career", string="Carrera", related="student_id.career_id",
        store=True, index=True
    )

    # ----------------- Helpers cfg -----------------
    @api.model
    def _get_cfg_int(self, key, default):
        ICP = self.env["ir.config_parameter"].sudo()
        try:
            return int(ICP.get_param(key, default))
        except Exception:
            return int(default)

    @api.model
    def _default_source(self):
        ICP = self.env["ir.config_parameter"].sudo()
        return ICP.get_param("reading_access.default_source", "kiosk")

    @api.model
    def _default_campus(self):
        user = self.env.user
        campuses = user.sudo().crai_campus_ids
        return campuses[0].id if len(campuses) == 1 else False

    # ----------------- Guard rails -----------------
    @api.model_create_multi
    def create(self, vals_list):
        duplicate_seconds = self._get_cfg_int("reading_access.duplicate_window_seconds", 10)
        now = fields.Datetime.now()
        res = self.browse()
        for vals in vals_list:
            sid = vals.get("student_id")
            if not sid:
                raise ValidationError(_("Student is required."))

            # Anti-duplicado: evita doble IN inmediato
            last = self.search([("student_id", "=", sid)], order="occurred_at desc", limit=1)
            if last and (now - last.occurred_at).total_seconds() < duplicate_seconds:
                raise ValidationError(
                    _("Duplicate scan ignored (anti-duplicate window: %s sec).") % duplicate_seconds
                )

            vals.setdefault("operator_id", self.env.user.id)
            res |= super(ReadingAccess, self).create(vals)
        return res

    def write(self, vals):
        if "operator_id" in vals and not self.env.user.has_group("crai_base.group_crai_admin"):
            raise UserError(_("Only Admin can change operator."))
        return super().write(vals)

    def unlink(self):
        """ Librarian:
            - sin borrado masivo
            - solo dentro de 10 minutos desde occurred_at
        """
        if self.env.user.has_group("crai_base.group_crai_librarian") and \
           not self.env.user.has_group("crai_base.group_crai_admin"):
            if len(self) > 1:
                raise UserError(_("Bulk delete is not allowed for librarians. Delete one record at a time."))
            minutes_limit = 10
            now = fields.Datetime.now()
            for rec in self:
                age = (now - (rec.occurred_at or now)).total_seconds() / 60.0
                if age > minutes_limit:
                    raise UserError(_("You can only delete within %s minutes of creation.") % minutes_limit)
        return super().unlink()

    # ----------------- API escaneo (solo IN) -----------------
    @api.model
    def scan_document(self, number_id, campus_id=False):
        """Escaneo de cédula → siempre crea IN (si no cae en anti-duplicado).
        Devuelve: dict(ok, message, record_id, student)
        """
        if not number_id:
            return {"ok": False, "message": _("Empty document number."), "record_id": False}

        Student = self.env["crai.student"].sudo()
        student = Student.find_by_document(number_id)
        if not student:
            return {"ok": False, "message": _("El estudiante no existe."), "record_id": False}

        if not campus_id:
            campus_id = self._default_campus()
        if not campus_id:
            return {"ok": False, "message": _("Seleccione una sede."), "record_id": False}

        # Librarian solo en sus sedes
        if self.env.user.has_group("crai_base.group_crai_librarian") and \
           not self.env.user.has_group("crai_base.group_crai_admin"):
            if campus_id not in self.env.user.sudo().crai_campus_ids.ids:
                return {"ok": False, "message": _("You are not allowed to operate this campus."), "record_id": False}

        duplicate_seconds = self._get_cfg_int("reading_access.duplicate_window_seconds", 10)
        default_source = self._default_source()

        now = fields.Datetime.now()
        last = self.search([("student_id", "=", student.id)], order="occurred_at desc", limit=1)
        if last and (now - last.occurred_at).total_seconds() < duplicate_seconds:
            return {
                "ok": False,
                "message": _("Duplicate scan ignored (within %s sec).") % duplicate_seconds,
                "record_id": last.id,
                "student": {"name": student.name, "career": getattr(student.career_id, "name", False)},
            }

        rec = self.create({
            "student_id": student.id,
            "campus_id": campus_id,
            "source": default_source or "kiosk",
            "occurred_at": now,
            "operator_id": self.env.user.id,
        })
        return {
            "ok": True,
            "message": _("Entry registered."),
            "record_id": rec.id,
            "student": {"name": student.name, "career": getattr(student.career_id, "name", False)},
        }


# ------------- Wizard Kiosk -------------
class ReadingKioskWizard(models.TransientModel):
    _name = "crai.reading.kiosk.wizard"
    _description = "Reading Kiosk Scan"

    campus_id = fields.Many2one("crai.campus", string="Campus", required=True)
    scan_input = fields.Char(string="Cédula")
    feedback_ok = fields.Boolean(readonly=True)
    feedback_message = fields.Char(readonly=True)
    student_name = fields.Char(readonly=True)
    career_name = fields.Char(readonly=True)
    student_home_campus_name = fields.Char(readonly=True)

    # AGREGAR ESTE ONCHANGE
    @api.onchange('scan_input')
    def _onchange_scan_input(self):
        """Se dispara automáticamente cuando el escáner ingresa el código"""
        if self.scan_input and len(self.scan_input.strip()) > 0:
            number = self.scan_input.strip()
            
            # ✅ NUEVO: Limpiar el código - extraer solo números
            import re
            clean_number = re.sub(r'\D', '', number)  # Elimina todo excepto dígitos
            
            # ✅ Validar que tenga al menos contenido
            if not clean_number:
                self.feedback_ok = False
                self.feedback_message = _("Código inválido: no contiene números.")
                self.scan_input = ""
                return
            
            # ✅ Opcional: Validar que tenga al menos 10 dígitos (cédula ecuatoriana)
            if len(clean_number) < 10:
                self.feedback_ok = False
                self.feedback_message = _("Código inválido: debe tener al menos 10 dígitos.")
                self.scan_input = ""
                return
            
            # ✅ Opcional: Tomar solo los primeros 10 dígitos
            if len(clean_number) > 10:
                clean_number = clean_number[:10]
            
            if not self.campus_id:
                self.feedback_ok = False
                self.feedback_message = _("Seleccione un campus primero.")
                self.scan_input = ""
                return
            
            Access = self.env["crai.reading.access"].sudo()
            # ✅ CAMBIO: Pasar el número limpio en lugar del original
            result = Access.scan_document(clean_number, self.campus_id.id)
            
            # Actualizar feedback
            self.feedback_ok = bool(result.get("ok"))
            self.feedback_message = result.get("message")
            
            student_data = result.get("student") or {}
            self.student_name = student_data.get("name")
            self.career_name = student_data.get("career")
            self.student_home_campus_name = student_data.get("home_campus")
            
            # Limpiar el campo para siguiente escaneo
            self.scan_input = ""

    def action_scan(self):
        # Mantener este método por si quieren usar el botón manualmente
        self.ensure_one()
        number = (self.scan_input or "").strip()
        if not number:
            new = self.create({
                "campus_id": self.campus_id.id,
                "feedback_ok": False,
                "feedback_message": _("Ingrese la cédula para escanear."),
            })
            return {
                "type": "ir.actions.act_window",
                "res_model": "crai.reading.kiosk.wizard",
                "view_mode": "form",
                "res_id": new.id,
                "target": "new",
            }

        Access = self.env["crai.reading.access"].sudo()
        result = Access.scan_document(number, self.campus_id.id)

        new = self.create({
            "campus_id": self.campus_id.id,
            "feedback_ok": bool(result.get("ok")),
            "feedback_message": result.get("message"),
            "student_name": (result.get("student") or {}).get("name"),
            "career_name": (result.get("student") or {}).get("career"),
            "student_home_campus_name": (result.get("student") or {}).get("home_campus"),
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "crai.reading.kiosk.wizard",
            "view_mode": "form",
            "res_id": new.id,
            "target": "new",
        }