import logging
from odoo import models, fields, api
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _inherit = ['notification.mixin']  # Heredamos el mixin de notificaciones
    _description = 'Library Cubicle Loan'

    barcode = fields.Char(string='Código de Barras', help="Escanea el código de barras del estudiante")
    student_id = fields.Many2one('student.profile', string='Estudiante')
    cubicle_id = fields.Many2one('library.cubicle', 
                                    string='Cubículo', 
                                    required=True,
                                    domain=lambda self: [
                                    ('campus_id', '=', self.env.user.campus_id.id)
                                ]
                                )
    campus_id = fields.Many2one('university.campus', 
                                    string='Sede',
                                    related='cubicle_id.campus_id',
                                    store=True
                                )
    user_id = fields.Many2one('res.users', string='Bibliotecario', default=lambda self: self.env.user, readonly=True)
    student_name = fields.Char(related='student_id.completename', string='Nombres del Estudiante', readonly=True)
    date= fields.Date(string="Fecha de Préstamo", store=True, compute="_compute_start_date")
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

    def _compute_start_date(self):
        for record in self:
            record.date = record.start_time.date() if record.start_time else False

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            student = self.env['student.profile'].search([('barcode', '=', self.barcode)], limit=1)
            if student:
                self.student_id = student.id
            else:
                raise ValidationError('No se encontró ningún estudiante con el código de barras ingresado.')
    
    @api.onchange('cubicle_id')
    def _onchange_cubicle_id(self):
        """Verifica si el cubículo está disponible antes de asignarlo."""
        if self.cubicle_id:
            # Verifica si el cubículo está ocupado
            if self.cubicle_id.status == 'occupied':
                if self.state == 'reserved':
                    # Buscar si hay un préstamo activo o una reserva en el mismo horario
                    existing_loan = self.env['library.loan'].search([
                        ('cubicle_id', '=', self.cubicle_id.id),
                        ('state', 'in', ['active', 'reserved']),  # También verifica reservas
                        ('start_time', '<=', self.start_time),
                        ('end_time', '>=', self.start_time)
                    ], limit=1)

                    if existing_loan:
                        self.send_notification(
                            title="Cubículo Ocupado",
                            message=f"El cubículo {self.cubicle_id.name} ya está reservado/ocupado hasta las {existing_loan.end_time}.",
                            sticky=False,
                            msg_type='warning'
                        )
                        self.cubicle_id = False  # Bloquea la selección del cubículo
                else:
                    self.send_notification(
                        title="Cubículo Ocupado",
                        message=f"El cubículo {self.cubicle_id.name} ya está ocupado, selecciona otro.",
                        sticky=False,
                        msg_type='warning'
                    )
                    self.cubicle_id = False  # Bloquea la selección del cubículo

    @api.depends('student_id', 'cubicle_id')
    def _compute_display_name(self):
        for record in self:
            student_name = record.student_id.completename if record.student_id else 'Sin Estudiante'
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

   
    @api.model
    def create(self, vals):
        """Controla la creación de préstamos y reservas asegurando que no haya conflictos de horarios."""

        cubicle_id = vals.get('cubicle_id')
        new_state = vals.get('state')  # Puede ser 'reserved' o 'active'

        # Buscamos el cubículo seleccionado
        cubicle = self.env['library.cubicle'].browse(cubicle_id)

        # Cambiar el estado del cubículo si se aprueba el préstamo o la reserva
        if new_state == 'reserved':
            cubicle.status = 'reserved'
        elif new_state == 'active':
            cubicle.status = 'occupied'

        # Llamamos a `super()` solo si todo está correcto
        loan = super(LibraryLoan, self).create(vals)

        # 🔔 Notificación de éxito
        loan.send_notification(
            title='Préstamo/Reserva exitoso',
            message=f'El cubículo ({cubicle.name}) fue {("prestado" if new_state == "active" else "reservado")} exitosamente a ({loan.student_id.completename}).',
            sticky=False,
            msg_type='success',
        )

        return loan


    def write(self, vals):
        """Sobreescribe el método write para gestionar los cambios de estado."""
        if vals.get('state') == 'returned':
            for record in self.filtered(lambda r: r.cubicle_id and r.state in ['active', 'overdue']):
                record.return_cubicle()
        else:
            self.send_notification(
                title="Problemas con la devolución",
                message=f"El registro {self.display_name} ha sido modificado",
                sticky=False,
                msg_type='warning',
            )

        return super(LibraryLoan, self).write(vals)

    def return_cubicle(self):
        self.ensure_one()
        
        if not self.cubicle_id:
            raise ValidationError("El préstamo no tiene un cubículo asociado.")

        # Buscar futuras reservas
        future_reservations = self.env['library.loan'].search([
            ('cubicle_id', '=', self.cubicle_id.id),
            ('state', '=', 'reserved'),
            ('start_time', '>=', self.end_time)
        ], limit=1)

        # Cambiar el estado del cubículo según la disponibilidad
        if future_reservations:
            self.cubicle_id.status = 'reserved'
        else:
            self.cubicle_id.status = 'available'
            
        self.send_notification(
            title="Devolución Exitosa",
            message=f"El préstamo del cubículo {self.cubicle_id.name} ha sido devuelto y ahora está {self.cubicle_id.status}.",
            sticky=False,
            msg_type='success',
        )

    @api.model
    def _auto_convert_reservations_to_loans(self):
        today_start = datetime.combine(fields.Date.today(), datetime.min.time())  # 00:00:00 de hoy
        today_end = today_start + timedelta(days=1) - timedelta(seconds=1)  # 23:59:59 de hoy

        reservations = self.search([
            ('state', '=', 'reserved'),
            ('start_time', '>=', today_start),
            ('start_time', '<=', today_end)  # Solo las de hoy
        ])

        for loan in reservations:
            loan.state = 'active'  # Cambiamos el estado a préstamo activo
            loan.cubicle_id.status = 'occupied'  # Marcamos el cubículo como ocupadoz

    @api.model
    def _check_overdue_loans(self):
        """Actualiza el estado de préstamos vencidos y notifica al bibliotecario correspondiente."""
        current_time = fields.Datetime.now()
        overdue_loans = self.search([
            ('state', '=', 'active'),
            ('end_time', '<', current_time)
        ])
        for loan in overdue_loans:
            loan.state = 'overdue'
            loan.send_notification(
                title="Préstamo Vencido",
                message=f'El préstamo del cubículo {loan.cubicle_id.name} para {loan.student_id.completename} ha vencido.',
                sticky=False,
                msg_type='success',
            )