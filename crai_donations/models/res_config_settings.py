# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    # Configuración de notificaciones
    donation_enable_email_notifications = fields.Boolean(
        string="Habilitar notificaciones por email",
        config_parameter="crai_donations.enable_email_notifications",
        default=True,
        help="Envía emails automáticos cuando cambia el estado de una donación"
    )
    
    # Email del aprobador principal (opcional)
    donation_approver_email = fields.Char(
        string="Email del Aprobador Principal",
        config_parameter="crai_donations.approver_email",
        help="Email adicional para notificaciones de nuevas solicitudes"
    )
    
    # Configuración de certificados
    donation_certificate_validity_days = fields.Integer(
        string="Días de validez del certificado",
        config_parameter="crai_donations.certificate_validity_days",
        default=0,
        help="Número de días de validez del certificado (0 = sin vencimiento)"
    )
