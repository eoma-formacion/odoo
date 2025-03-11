from odoo import models, fields, api


class RoomBooking(models.Model):
    _inherit = "room.booking"

    event_id = fields.Many2one("event.event", default=False)
