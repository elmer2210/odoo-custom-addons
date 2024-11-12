from odoo import models, fields, api

class Career(models.Model):
	_name = 'campus.career'
	_description = 'Career'

	code = fields.Char(string='Career Code', required=True)
	name = fields.Char(string='Career Name', required=True)
	campus_id = fields.Many2one('campus.campus', string='Campus', required=True)
	faculty_id = fields.Many2one('campus.faculty', string='Faculty', required=True)

	  # Definir el display_name para incluir tanto el nombre como el código
	display_name = fields.Char(compute='_compute_display_name', store=True)


	@api.depends('name', 'code')
	def _compute_display_name(self):
		for record in self:
			if record.code:
				record.display_name = f"{record.code}/{record.name}" 
			else:
				record.display_name = record.name

