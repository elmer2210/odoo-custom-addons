# -*- coding: utf-8 -*-
# from odoo import http


# class UniversityDashboard(http.Controller):
#     @http.route('/university_dashboard/university_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/university_dashboard/university_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('university_dashboard.listing', {
#             'root': '/university_dashboard/university_dashboard',
#             'objects': http.request.env['university_dashboard.university_dashboard'].search([]),
#         })

#     @http.route('/university_dashboard/university_dashboard/objects/<model("university_dashboard.university_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('university_dashboard.object', {
#             'object': obj
#         })

