# Archivo `library_loan.py` en `models`
from odoo import models, fields, api
from datetime import datetime, timedelta

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Library Cubicle Loan'

    cubicle_id = fields.Many2one('library.cubicle', string='Cubículo', required=True)
    user_id = fields.Many2one('res.users', string='Bibliotecario', default=lambda self: self.env.user, readonly=True)
    student_id = fields.Many2one('student_management.student_profile', string='Estudiante', required=True)
    student_code = fields.Char(related='student_id.student_id', string='Código del Estudiante', readonly=True)
    start_time = fields.Datetime(string='Fecha y Hora de Inicio', default=fields.Datetime.now, required=True)
    end_time = fields.Datetime(string='Fecha y Hora de Fin', compute='_compute_end_time', store=True)
    state = fields.Selection([
        ('active', 'Activo'),
        ('returned', 'Devuelto'),
        ('overdue', 'Tiempo Excedido')
    ], string='Estado del Préstamo', default='active', required=True)

    @api.depends('start_time')
    def _compute_end_time(self):
        for record in self:
            record.end_time = record.start_time + timedelta(hours=4)

    @api.constrains('cubicle_id')
    def _check_cubicle_availability(self):
        for record in self:
            if record.cubicle_id.status != 'available':
                raise UserError('El cubículo seleccionado no está disponible para préstamo.')
            record.cubicle_id.status = 'occupied'

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

#### 10.2 Lógica de Alerta para Préstamos Vencidos Vamos a añadir un método que se ejecute como parte del cron job para marcar como **vencidos** aquellos préstamos cuyo plazo haya pasado:```python
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
