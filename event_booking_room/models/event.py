from odoo import models, fields, api


class Event(models.Model):
    _inherit = "event.event"

    room_booking_ids = fields.One2many("room.booking", "event_id")
