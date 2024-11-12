from odoo import models, fields

class Student(models.Model):
	_name = 'student.student'
	_description = 'Student Information'

	name = fields.Char(string='Student Name', required=True)
	barcode = fields.Char(string='Barcode', required=True)
	is_disabled = fields.Boolean(string='Has Disability')
	career_id = fields.Many2one('campus.career', string='Career', required=True)
	period_academic = fields.Char(string='Academic Period')
	email = fields.Char(string='Email')
	disability_type=fields.Selection(selection=[
					('physics','Discapacidad física'),
					('sensory','Discapacidad sensorial'),
					('intellectual', 'Discapacidad intelectual'),
					('psichic', 'Discapacidad Psíquica'),
					('visceral','Discapacidad Visceral'),
					], string='Disability Type', requiered=True, default='physics')

	 # Campos relacionados
	faculty_id = fields.Many2one('campus.faculty', string='Faculty', related='career_id.faculty_id', store=True)
	campus_id = fields.Many2one('campus.campus', string='Campus', related='career_id.campus_id', store=True)


