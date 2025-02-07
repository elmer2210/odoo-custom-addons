from odoo import models, fields, api

class StudentEntry(models.Model):
    _name = 'student_entry.student_computer'
    _description = 'Uso de equipos'
    _order = 'init_time desc'
    
    numberID = fields.Char(string='Número de cédula', required=True, help="Ingrese el número de cédula")
    email = fields.Char(string='Correo Electrónico', required=True, help="Ingrese el número de cédula")
    student_id = fields.Many2one(
        'student_management.student_profile',
        string='Estudiante',
        readonly=True,
        store=True,
    )
    init_time = fields.Datetime(string='Fecha y Hora de Inicio', default=fields.Datetime.now, required=True)
    finit_time = fields.Datetime(string='Fecha y Hora de Fin')
    campus_id = fields.Many2one('student_management.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('student_management.career', string='Carrera', related='student_id.career_id', store=True)

    