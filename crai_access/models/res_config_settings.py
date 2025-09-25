# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ra_duplicate_window_seconds = fields.Integer(
        string="Duplicate window (seconds)",
        config_parameter="reading_access.duplicate_window_seconds",
        default=10,
        help="Evita doble registro por escaneos consecutivos."
    )
    ra_default_source = fields.Selection(
        [("kiosk", "Kiosk"), ("manual", "Manual")],
        string="Default Source",
        config_parameter="reading_access.default_source",
        default="kiosk"
    )
