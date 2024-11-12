from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LibraryAccess(models.Model):
	_name = 'library.access'
	_description = 'Student Access to Library and Cubicle'

	student_id = fields.Many2one('student.student', string='Student')
	barcode = fields.Char(string='Barcode', required=True)
	access_date = fields.Datetime(string='Access Time', default=fields.Datetime.now, readonly=True)

	# Campos relacionados para carrera y facultad
	campus_id = fields.Many2one(related='student_id.campus_id', string='Library Campus', store=True, readonly=True)
	career_id = fields.Many2one(related='student_id.career_id', string='Career', store=True, readonly=True)
	faculty_id = fields.Many2one(related='student_id.career_id.faculty_id', string='Faculty', store=True, readonly=True)

	@api.onchange('barcode')
	def _onchange_barcode(self):
		# Si hay un código de barras ingresado
		if self.barcode:
			# Buscar el estudiante con el código de barras
			student = self.env['student.student'].search([('barcode', '=', self.barcode)], limit=1)
			if student:
				self.student_id = student
				# Limpiar el campo barcode después de asignar el estudiante
				self.barcode = ""
			else:
				# Si no se encuentra estudiante, lanzar una excepción
				self.student_id = False
				raise ValidationError("No se encontró un estudiante con ese código de barras.")
		else:
			self.student_id = False

	@api.model
	def create(self, vals):
		if 'barcode' in vals:
			# Buscar el estudiante por el código de barras
			student = self.env['student.student'].search([('barcode', '=', vals['barcode'])], limit=1)
			if student:
				vals['student_id'] = student.id
				# Limpiar el código de barras después de registrar
				vals['barcode'] = ""
			else:
				raise ValidationError("No se encontró un estudiante con ese código de barras.")
		return super(LibraryAccess, self).create(vals)

	def write(self, vals):
		if 'barcode' in vals:
			# Buscar el estudiante por el código de barras
			student = self.env['student.student'].search([('barcode', '=', vals['barcode'])], limit=1)
			if student:
				vals['student_id'] = student.id
				# Limpiar el código de barras después de registrar
				vals['barcode'] = ""
			else:
				raise ValidationError("No se encontró un estudiante con ese código de barras.")
		return super(LibraryAccess, self).write(vals)
