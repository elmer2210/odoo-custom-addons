# -*- coding: utf-8 -*-
# from odoo import http


# class StudnentDashboard(http.Controller):
#     @http.route('/studnent_dashboard/studnent_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/studnent_dashboard/studnent_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('studnent_dashboard.listing', {
#             'root': '/studnent_dashboard/studnent_dashboard',
#             'objects': http.request.env['studnent_dashboard.studnent_dashboard'].search([]),
#         })

#     @http.route('/studnent_dashboard/studnent_dashboard/objects/<model("studnent_dashboard.studnent_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('studnent_dashboard.object', {
#             'object': obj
#         })

