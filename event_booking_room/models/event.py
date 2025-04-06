from odoo import models, fields, api
from datetime import datetime


class Event(models.Model):
    _inherit = "event.event"

    room_booking_ids = fields.One2many("room.booking", "event_id")
    instructor_ids = fields.Many2many("res.partner", string="Ponentes")
    room_booking_count = fields.Integer(
        string="Calendario", compute="_compute_room_booking_count"
    )
    link_dossier = fields.Char(
        string="Link a Dossier",
        help="Enlace al dossier de la actividad, si existe.",
    )

    def _compute_room_booking_count(self):
        for event in self:
            event.room_booking_count = len(event.room_booking_ids)

    def action_view_room_bookings(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Calendario",
            "view_mode": "calendar,gantt",
            "res_model": "room.booking",
            "domain": [("event_id", "=", self.id)],
            "context": {
                "initial_date": self.date_begin,
                **self.env.context,
            },
        }

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        current_datetime = datetime.now()
        duration = self.date_end - self.date_begin

        default.update(
            {
                "date_begin": current_datetime,
                "date_end": current_datetime + duration,
                "room_booking_ids": [
                    (
                        0,
                        0,
                        {
                            "name": booking.name,
                            "room_id": booking.room_id.id,
                            "start_datetime": current_datetime
                            + (booking.start_datetime - self.date_begin),
                            "stop_datetime": current_datetime
                            + (booking.stop_datetime - self.date_begin),
                            # Añadir otros campos necesarios aquí
                        },
                    )
                    for booking in self.room_booking_ids
                ],
            }
        )
        return super(Event, self).copy(default)
