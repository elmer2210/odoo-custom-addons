from odoo import http
from odoo.http import request

class CustomDashboard(http.Controller):
    
    @http.route('/web', type='http', auth='user', website=False)
    def redirect_to_dashboard(self):
        """ Redirige la URL principal `/web` a la vista del escritorio de apps """
        return request.redirect('/web#menu_id=15')
