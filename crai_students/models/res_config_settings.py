from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
        self.ensure_one()
        res = self.env["crai.students.ingest.service"].run_ingest(dry_run=True)
        msg = _(
            "Dry-run completado.\n"
            "Total recibidos: %(total)s\n"
            "Nuevos (crear): %(create)s\n"
            "Existentes (omitidos): %(skip)s\n"
            "Errores: %(errors)s"
        ) % res
        raise UserError(msg)  # Mensaje rápido en pop-up
