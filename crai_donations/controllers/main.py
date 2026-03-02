from odoo import http
from odoo.http import request

class CraiCertificateVerification(http.Controller):

    @http.route(['/web/crai/verificar'], type='http', auth="public")
    def verify_certificate(self, code=None, **kwargs):
        # Capturamos el código
        search_code = code or kwargs.get('code', '').strip()

        # UNIFICAMOS TODO AQUÍ: Datos de búsqueda + El "engaño" del idioma
        values = {
            'search_code': search_code,
            'certificate': False,
            'error': False,
            'searched': False,
            'languages': [('es_EC', 'Español')],
            'lang': 'es_EC',
        }

        if search_code:
            values['searched'] = True

            # Búsqueda con permisos de superusuario
            certificate = request.env['crai.donation'].sudo().search([
                ('certificate_code', '=', search_code),
                ('state', '=', 'certificate_issued') 
            ], limit=1)

            if certificate:
                values['certificate'] = certificate
            else:
                values['error'] = True

        # Ahora sí, enviamos los datos correctos y completos
        return request.render("crai_donations.certificate_verification_page", values)
