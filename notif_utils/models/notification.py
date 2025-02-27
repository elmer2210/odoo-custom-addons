from odoo import models, fields

class NotificationMixin(models.AbstractModel):
    _name = 'notification.mixin'
    _description = 'Mixin for Sending Notifications'

    def send_notification(self, title, message, sticky=False, msg_type='info'):
        """Envía una notificación emergente al usuario."""
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',  # Ahora usamos el ID del usuario directamente
            {
                'title': title,
                'message': message,
                'sticky': sticky,
                'type': msg_type,
            }
        )
        return True

    def send_message(self, user, body, subject='Mensaje del Sistema'):
        """Envía un mensaje al chat interno de Odoo sin necesidad de `res.partner`."""
        message = self.env['mail.message'].create({
            'message_type': 'notification',
            'body': body,
            'subject': subject,
            'model': 'res.users',  # Se vincula a `res.users` en lugar de `res.partner`
            'res_id': user.id,  # Ahora apunta directamente al usuario
        })

         # Crear la notificación para que aparezca en la bandeja de entrada
        self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': user.partner_id.id,
            'notification_type': 'inbox',  # Notificación en bandeja de entrada
            'is_read': False,
        })

        return message