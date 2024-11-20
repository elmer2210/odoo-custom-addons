from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentEntry(models.Model):
    _name = 'student.entry'
    _inherit = ['mail.thread']  # Herencia de mail.thread
    _description = 'Registro de Ingresos de Estudiantes'
    _order = 'entry_time desc'
    
    barcode = fields.Char(string='Código de Barras', required=True, help="Escanee el código de barras del estudiante")
    student_id = fields.Many2one(
        'student_management.student_profile',
        string='Estudiante',
        readonly=True,
        store=True,
    )
    entry_time = fields.Datetime(string='Fecha y Hora de Ingreso', default=fields.Datetime.now, required=True)
    campus_id = fields.Many2one('student_management.campus', string='Sede', related='student_id.campus_id', store=True)
    faculty_id = fields.Many2one('student_management.faculty', string='Facultad', related='student_id.faculty_id', store=True)
    career_id = fields.Many2one('student_management.career', string='Carrera', related='student_id.career_id', store=True)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            student = self.env['student_management.student_profile'].search([('barcode', '=', self.barcode)], limit=1)
            if student and student.active:
                self.student_id = student
                # Registrar el ingreso automáticamente
                self.create({
                    'barcode': self.barcode,
                    'student_id': student.id,
                    'entry_time': fields.Datetime.now(),
                })
                 # Mostrar un mensaje como notificación menos intrusiva
                self.env['bus.bus']._sendone(
                    self.env.user.partner_id,
                    'simple_notification',
                    {
                        'title': 'Registro Exitoso',
                        'message': f'Ingreso registrado correctamente para el estudiante: {student.name}',
                        'sticky': False,  # False hará que la notificación desaparezca automáticamente
                        'type': 'success',
                    }
                )
                # Vaciar el campo de código de barras después del registro
                self.barcode = ''
            else:
                # Enviar notificación al administrador en caso de error
                admin_user = self.env.ref('base.user_admin')  # Obtener el usuario administrador (predeterminado)
                subject = 'Error en el registro de ingreso de estudiante'
                body = f'El estudiante con el código de barras {self.barcode} no existe o está inactivo. Por favor, verifica este incidente.'

                 # Crear el mensaje usando mail.message.create()
                self.env['mail.message'].create({
                    'subject': subject,
                    'body': body,
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'partner_ids': [(4, admin_user.partner_id.id)],
                })

                self.env['bus.bus']._sendone(
                    self.env.user.partner_id,
                    'simple_notification',
                    {
                        'title': 'Problemas con el código de barras',
                        'message': f'El código de barras {self.barcode} no existe o estudiante inactivo',
                        'sticky': False,  # False hará que la notificación desaparezca automáticamente
                        'type': 'danger',
                    }
                )
                # Vaciar el campo de código de barras después del registro
                self.barcode = ''
