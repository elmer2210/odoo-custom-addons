from odoo import models, fields

class LibraryCubicle(models.Model):
    _name = 'library.cubicle'
    _description = 'Library Cubicle'

    name = fields.Char(string='Número del Cubículo', required=True)
    campus_id = fields.Many2one('student_management.campus', string='Campus', required=True)  # Ahora usamos campus_id en lugar de branch_id
    cubicle_type = fields.Selection([
        ('meeting', 'Reunión o Tareas (Mesas y Sillas)'),
        ('computer', 'Equipado con Computadora (Reuniones Online, Tareas con Audio/Video)')
    ], string='Tipo de Cubículo', required=True)
    status = fields.Selection([
        ('available', 'Disponible'),
        ('reserved', 'Reservado'),
        ('occupied', 'Ocupado'),
        ('maintenance', 'En Mantenimiento')
    ], string='Estado', default='available', required=True)
    disability_preference = fields.Boolean(string='Preferencia para Personas con Discapacidad')