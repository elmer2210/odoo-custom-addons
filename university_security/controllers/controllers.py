# -*- coding: utf-8 -*-
# from odoo import http


# class UniversitySecurity(http.Controller):
#     @http.route('/university_security/university_security', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/university_security/university_security/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('university_security.listing', {
#             'root': '/university_security/university_security',
#             'objects': http.request.env['university_security.university_security'].search([]),
#         })

#     @http.route('/university_security/university_security/objects/<model("university_security.university_security"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('university_security.object', {
#             'object': obj
#         })

