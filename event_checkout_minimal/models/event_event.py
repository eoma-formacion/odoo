from odoo import models, fields


class EventEvent(models.Model):
    _inherit = 'event.event'

    event_banner = fields.Image(
        string='Banner del Evento',
        help='Imagen de banner que se mostrará en el encabezado de la tarjeta del formulario de registro'
    )