from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr

import logging
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crai_api_url = fields.Char(
        string="URL API Estudiantes (GET)",
        config_parameter="crai_students.api_url",
        help="Endpoint que retorna JSON con clave 'data' (lista de estudiantes)."
    )
    crai_api_token = fields.Char(
        string="Token Bearer (opcional)",
        config_parameter="crai_students.api_token",
        help="Se envía como Authorization: Bearer <token> si se llena."
    )

    def action_dry_run_students_import(self):
        """Prueba sin crear: muestra cuántos CREARÍA y cuántos omitiría."""
        try:
            self.ensure_one()
            res = self.env["crai.students.ingest.service"].run_ingest(
                dry_run=True, 
                update_existing=True
            )
            msg = _(
                "Dry-run completado.\n"
                "Total recibidos: %(total)s\n"
                "Nuevos (crear): %(create)s\n"
                "Actualizados: %(update)s\n"
                "Existentes (omitidos): %(skip)s\n"
                "Errores: %(errors)s"
            ) % res
            
            # Retornar notificación en lugar de UserError
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Dry-run completado"),
                    'message': msg,
                    'type': 'info',
                    'sticky': True,  # Para que el usuario pueda leerlo con calma
                }
            }
            
        except Exception as e:
            _logger.exception("CRAI DRY-RUN error")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error en dry-run"),
                    'message': ustr(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_update_students_import(self):
        """Ejecuta la importación real: crea/actualiza estudiantes."""
        try:
            self.ensure_one()
            res = self.env["crai.students.ingest.service"].run_ingest(
                dry_run=False, 
                update_existing=True
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Actualización completada"),
                    'message': _(
                        "Total: %(total)s | Creados: %(create)s | Actualizados: %(update)s | "
                        "Omitidos: %(skip)s | Errores: %(errors)s"
                    ) % res,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.exception("CRAI UPDATE error")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error al actualizar"),
                    'message': ustr(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
