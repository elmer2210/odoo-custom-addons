from odoo import models, fields, api

class StudentEntry(models.Model):
    _name = 'library.computer'
    _description = 'Uso de equipos'
    _order = 'init_time desc'
    
    numberID = fields.Char(string='Número de cédula', required=True, help="Ingrese el número de cédula")
    email = fields.Char(string='Correo Electrónico', required=True, help="Ingrese el correo electrónico")
    student_id = fields.Many2one(
        'student.profile',
        string='Estudiante',
        readonly=True,
        store=True,
    )
    init_time = fields.Datetime(string='Fecha y Hora de Inicio', default=fields.Datetime.now, required=True)
    finit_time = fields.Datetime(string='Fecha y Hora de Fin')
    total_time = fields.Char("Tiempo Total de Uso (Horas)", compute="_compute_total_time", store=True)
    campus_id = fields.Many2one('university.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('university.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('university.career', string='Carrera', related='student_id.career_id', store=True)

    @api.depends('init_time', 'finit_time')
    def _compute_total_time(self):
        for record in self:
            if record.init_time and record.finit_time:
                delta = record.finit_time - record.init_time
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes = remainder // 60
                record.total_time = f"0{int(hours)}:{int(minutes)}"
        else:
            record.total_time = "00:00"