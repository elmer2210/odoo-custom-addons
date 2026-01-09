# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crai_session_timeout_minutes = fields.Integer(
        string="Timeout de inactividad (minutos)",
        config_parameter="crai_computers.session_timeout_minutes",
        default=15,
        help="Si no hay heartbeat en este tiempo, la sesión se cierra automáticamente por inactividad. Recomendado: 10-15 minutos."
    )
    
    crai_heartbeat_interval_seconds = fields.Integer(
        string="Intervalo de heartbeat (segundos)",
        config_parameter="crai_computers.heartbeat_interval_seconds",
        default=60,
        help="Cada cuántos segundos la app debe enviar un heartbeat. Recomendado: 60 segundos."
    )