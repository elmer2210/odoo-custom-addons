from odoo import models, fields, api

class StudentEntry(models.Model):
    _name = 'library.entry'
    _inherit = ['notification.mixin']  # Herencia de mail.thread
    _description = 'Ingresos de Estudiantes'
    _order = 'entry_time desc'
    
    barcode = fields.Char(string='Código de Barras', required=True, help="Escanee el código de barras del estudiante")
    student_id = fields.Many2one(
        'student.profile',
        string='Estudiante',
        readonly=True,
        store=True,
    )
    entry_time = fields.Datetime(string='Fecha y Hora de Ingreso', default=fields.Datetime.now, required=True)
    campus_id = fields.Many2one('university.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('university.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('university.career', string='Carrera', related='student_id.career_id', store=True)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            student = self.env['student.profile'].search([('barcode', '=', self.barcode)], limit=1)
            if student and student.active:
                self.student_id = student
                # Registrar el ingreso automáticamente
                self.create({
                    'barcode': self.barcode,
                    'student_id': student.id,
                    'entry_time': fields.Datetime.now(),
                })
                 # Mostrar un mensaje como notificación menos intrusiva
                self.send_notification(
                    title= 'Registro Exitoso',
                    message= f'Ingreso registrado correctamente para el estudiante: {student.completename}',
                    sticky= False,  # False hará que la notificación desaparezca automáticamente
                    msg_type='success'
                )
                # Vaciar el campo de código de barras después del registro
                self.barcode = ''
            else:
                # Enviar notificación al administrador en caso de error
                admin_user = self.env.ref('base.user_admin')  # Obtener el usuario administrador (predeterminado)
                subject = 'Error en el registro de ingreso de estudiante'
                body = f'El estudiante con el código de barras {self.barcode} no existe o está inactivo. Por favor, verifica este incidente.'
                self.send_notification(
                    title= 'Problemas con el código de barras',
                    message=  f'El código de barras {self.barcode} no existe o estudiante inactivo',
                    sticky= False,  # False hará que la notificación desaparezca automáticamente
                    msg_type='danger'
                )
                 # Crear el mensaje usando mail.message.create()
                self.send_message(
                    admin_user,
                    body=body,
                    subject=subject
                )
                # Vaciar el campo de código de barras después del registro
                self.barcode = ''
