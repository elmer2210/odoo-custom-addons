# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class CraiComputer(models.Model):
    _name = "crai.computer"
    _description = "CRAI Computer"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, index=True, tracking=True)
    site_id = fields.Many2one("crai.site", string="Sede", index=True)
    campus_id = fields.Many2one("crai.campus", string="Campus", index=True)
    is_active = fields.Boolean(default=True, tracking=True)

    # NUEVO: relación explícita para depender de cambios en sesiones
    session_ids = fields.One2many(
        "crai.computer.session", "computer_id", string="Sesiones"
    )

    current_session_id = fields.Many2one(
        "crai.computer.session",
        string="Sesión activa",
        compute="_compute_current_session",
        store=False,
    )
    active_session_count = fields.Integer(
        compute="_compute_current_session",
        store=False,
        string="Sesiones abiertas"
    )

    _sql_constraints = [
        ("computer_code_unique", "unique(code)", "El código de equipo debe ser único."),
    ]

    # ✅ Depende de los estados de las sesiones asociadas (NO de 'id')
    @api.depends("session_ids.state")
    def _compute_current_session(self):
        for rec in self:
            # filtrar en memoria es suficiente; opcional: sorted por start_at
            open_sessions = [s for s in rec.session_ids if s.state == "open"]
            rec.active_session_count = len(open_sessions)
            rec.current_session_id = open_sessions[0].id if open_sessions else False
