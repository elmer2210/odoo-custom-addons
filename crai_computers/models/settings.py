# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crai_session_timeout_minutes = fields.Integer(
        string="Tiempo de inactividad (min)",
        config_parameter="crai_computers.session_timeout_minutes",
        default=2,
        help="Si no hay heartbeat en este tiempo, la sesión se cierra por inactividad."
    )
