# -*- coding: utf-8 -*-
# from odoo import http


# class LibraryDonations(http.Controller):
#     @http.route('/library_donations/library_donations', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/library_donations/library_donations/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('library_donations.listing', {
#             'root': '/library_donations/library_donations',
#             'objects': http.request.env['library_donations.library_donations'].search([]),
#         })

#     @http.route('/library_donations/library_donations/objects/<model("library_donations.library_donations"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('library_donations.object', {
#             'object': obj
#         })

