# -*- coding: utf-8 -*-
# from odoo import http


# class UniversityStudents(http.Controller):
#     @http.route('/university_students/university_students', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/university_students/university_students/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('university_students.listing', {
#             'root': '/university_students/university_students',
#             'objects': http.request.env['university_students.university_students'].search([]),
#         })

#     @http.route('/university_students/university_students/objects/<model("university_students.university_students"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('university_students.object', {
#             'object': obj
#         })

