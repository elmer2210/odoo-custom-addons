from odoo import models, fields

class Faculty(models.Model):
	_name = 'campus.faculty'
	_description = 'Faculty'

	code = fields.Char(string='Faculty Code', required=True)
	name = fields.Char(string='Faculty Name', required=True)
