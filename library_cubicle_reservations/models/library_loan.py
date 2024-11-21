from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Library Cubicle Loan'

    barcode = fields.Char(string='Código de Barras', help="Escanea el código de barras del estudiante")
    student_id = fields.Many2one('student_management.student_profile', string='Estudiante', required=True)
    cubicle_id = fields.Many2one('library.cubicle', string='Cubículo', required=True)
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
                raise UserError(f'El cubículo {record.cubicle_id.name} no está disponible en el horario solicitado. Ya está reservado entre {overlapping_loans[0].start_time} y {overlapping_loans[0].end_time}.')

    def return_cubicle(self):
        self.ensure_one()
        if self.state == 'active':
            self.state = 'returned'
            self.cubicle_id.status = 'available'
        else:
            raise UserError('El préstamo no está activo o ya fue devuelto.')

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