from odoo import models, fields

class DisabilityType(models.Model):
    _name = 'student.disability'
    _description = 'Tipo de Discapacidad'

    name = fields.Char(string='Tipo de Discapacidad', required=True)
    code = fields.Char(string='Código', required=False)
    description = fields.Text(string='Descripción', required=False)
