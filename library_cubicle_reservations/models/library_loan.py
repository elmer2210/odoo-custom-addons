from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _inherit = ['notification.mixin']  # Heredamos el mixin de notificaciones
    _description = 'Library Cubicle Loan'

    barcode = fields.Char(string='Código de Barras', help="Escanea el código de barras del estudiante")
    student_id = fields.Many2one('student_management.student_profile', string='Estudiante')
    cubicle_id = fields.Many2one('library.cubicle', 
                                 string='Cubículo', 
                                 required=True,
                                 domain=lambda self: [('campus_id', '=', self.env.user.campus_id.id)]
                                )
    user_id = fields.Many2one('res.users', string='Bibliotecario', default=lambda self: self.env.user, readonly=True)
    student_name = fields.Char(related='student_id.name', string='Nombres del Estudiante', readonly=True)
    start_time = fields.Datetime(string='Fecha y Hora de Inicio', default=fields.Datetime.now, required=True)
    end_time = fields.Datetime(string='Fecha y Hora de Fin', compute='_compute_end_time', store=True)
    state = fields.Selection([
        ('active', 'Activo'),
        ('reserved', 'Reservado'),
        ('returned', 'Devuelto'),
        ('overdue', 'Tiempo Excedido')
    ], string='Estado del Préstamo', required=True)

    color = fields.Integer(string='Color', compute='_compute_color')

    # Campo Calculado para el Nombre del Evento
    display_name = fields.Char(string='Nombre de la Reserva', compute='_compute_display_name', store=True)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            student = self.env['student_management.student_profile'].search([('barcode', '=', self.barcode)], limit=1)
            if student:
                self.student_id = student.id
            else:
                raise ValidationError('No se encontró ningún estudiante con el código de barras ingresado.')

    @api.depends('student_id', 'cubicle_id')
    def _compute_display_name(self):
        for record in self:
            student_name = record.student_id.name if record.student_id else 'Sin Estudiante'
            cubicle_name = record.cubicle_id.name if record.cubicle_id else 'Sin Cubículo'
            record.display_name = f'{student_name} - {cubicle_name}'

    @api.depends('state')
    def _compute_color(self):
        for record in self:
            if record.state == 'active':
                record.color = 10  # Verde
            elif record.state == 'reserved':
                record.color = 3  # Amarillo
            elif record.state == 'returned':
                record.color = 1  # Rojo
            elif record.state == 'overdue':
                record.color = 5  #Morado 
            else:
                record.color = 0  # Color por defecto

    @api.depends('start_time')
    def _compute_end_time(self):
        for record in self:
            record.end_time = record.start_time + timedelta(hours=4)

    @api.constrains('cubicle_id', 'start_time', 'end_time')
    def _check_cubicle_availability(self):
        for record in self:
            overlapping_loans = self.env['library.loan'].search([
                ('cubicle_id', '=', record.cubicle_id.id),
                ('state', '=', 'active'),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
                ('id', '!=', record.id)
            ])
            if overlapping_loans:

                 #notificamos el problema
                self.send_notification(
                    title= 'Disponibilidad de hora',
                    message= f'El cubículo {record.cubicle_id.name} no está disponible en el horario solicitado. Ya está reservado entre {overlapping_loans[0].start_time} y {overlapping_loans[0].end_time}.',
                    sticky= False,  # False hará que la notificación desaparezca automáticamente
                    msg_type='warning',
                )
            
    @api.model
    def create(self, vals):
        """Método para cambiar el estado del cubículo a ocupado cuando se cree un préstamo o reserva sin solapamientos."""
        
        # Obtener datos del cubículo y los horarios
        cubicle_id = vals.get('cubicle_id')
        start_time = vals.get('start_time')
        end_time = vals.get('end_time')

        # Buscamos el cubículo seleccionado
        cubicle = self.env['library.cubicle'].browse(cubicle_id)
        
        # Verificamos si hay colisiones de horarios
        overlapping_loans = self.env['library.loan'].search([
            ('cubicle_id', '=', cubicle_id),
            ('state', 'in', ['active', 'overdue']),  # Préstamos activos o vencidos (que aún no fueron devueltos)
            ('start_time', '<', end_time),
            ('end_time', '>', start_time)
        ])

        if overlapping_loans:
            # Notificamos el problema al bibliotecario
            self.send_notification(
                title='Problemas en el préstamo/reserva',
                message=f'El cubículo seleccionado ({cubicle.name}) ya está reservado o prestado en el mismo horario. Por favor, elija un horario diferente.',
                sticky=False,
                msg_type='warning',
            )
            # Lanzamos un error para evitar la creación del préstamo.
            raise UserError(f'El cubículo seleccionado ({cubicle.name}) ya está reservado o prestado en el mismo horario.')

        # Cambiamos el estado del cubículo a ocupado si no hay conflictos de horarios
        cubicle.status = 'occupied'

        # Creamos el préstamo o la reserva.
        loan = super(LibraryLoan, self).create(vals)

        # Notificamos la acción de creación exitosa.
        loan.send_notification(
            title='Préstamo/Reserva exitoso',
            message=f'El cubículo ({cubicle.name}) fue prestado o reservado exitosamente a ({loan.student_id.name}).',
            sticky=False,
            msg_type='success',
        )

        return loan

    def write(self, vals):
        """Sobreescribir el método write para gestionar los cambios de estado."""
        result = super(LibraryLoan, self).write(vals)
        
        # Lógica para devolver el cubículo si el estado se establece en 'returned'
        if 'state' in vals and vals['state'] == 'returned':
            for record in self:
                record.return_cubicle()
        return result
    
    def return_cubicle(self):
        self.ensure_one()
        if self.state == 'active':
            self.state = 'returned'
            self.cubicle_id.status = 'available'
        else:
            self.send_notification(
                title= 'Información',
                message= 'El préstamo no está activo o ya fue devuelto.',
                sticky= False,  # False hará que la notificación desaparezca automáticamente
                msg_type='success',
            )

    @api.model
    def _notify_expiring_loans(self):
        """Envía una notificación a los bibliotecarios para préstamos próximos a vencer."""
        current_time = fields.Datetime.now()
        warning_time = current_time + timedelta(hours=1)
        loans = self.search([('end_time', '<=', warning_time), ('state', '=', 'active')])
        for loan in loans:
            loan.user_id.notify_info(
                message=f'El préstamo del cubículo {loan.cubicle_id.name} para el estudiante {loan.student_id.name} está próximo a vencer.',
                title='Aviso de Préstamo Próximo a Vencer',
            )

    @api.model
    def _check_overdue_loans(self):
        """Actualiza el estado de préstamos vencidos y notifica al bibliotecario correspondiente."""
        current_time = fields.Datetime.now()
        overdue_loans = self.search([('end_time', '<', current_time), ('state', '=', 'active')])
        for loan in overdue_loans:
            loan.state = 'overdue'
            loan.user_id.notify_warning(
                message=f'El préstamo del cubículo {loan.cubicle_id.name} para el estudiante {loan.student_id.name} ha vencido. Por favor, contacte al estudiante para la devolución.',
                title='Aviso de Préstamo Vencido',
            )