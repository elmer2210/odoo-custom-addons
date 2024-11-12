from odoo import models, fields

class Faculty(models.Model):
	_name = 'campus.campus'
	_description = 'Campus University'

	code = fields.Char(string='Campus Code', required=True)
	name = fields.Char(string='Campus Name', required=True)
