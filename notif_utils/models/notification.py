from odoo import models, fields

class NotificationMixin(models.AbstractModel):
    _name = 'notification.mixin'
    _description = 'Mixin for Sending Notifications'

    def send_notification(self, title, message, sticky=False, msg_type='info'):
        """Method to send notifications to the user's screen."""
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': title,
                'message': message,
                'sticky': sticky,
                'type': msg_type,
            }
        )
