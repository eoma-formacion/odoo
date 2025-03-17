import pytz
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RoomBooking(models.Model):
    _inherit = "room.booking"

    event_id = fields.Many2one("event.event", default=False)

    @api.constrains("start_datetime", "stop_datetime")
    def _check_unique_slot(self):
        if not self.event_id:
            return super()._check_unique_slot()

        min_start = min(self.mapped("start_datetime"))
        max_stop = max(self.mapped("stop_datetime"))
        bookings_by_room = self.search(
            [
                ("room_id", "in", self.room_id.ids),
                ("start_datetime", "<", max_stop),
                ("stop_datetime", ">", min_start),
            ]
        ).grouped("room_id")
        for booking in self:
            if bookings_by_room.get(booking.room_id) and bookings_by_room[
                booking.room_id
            ].filtered(
                lambda b: b.id != booking.id
                and b.start_datetime < booking.stop_datetime
                and b.stop_datetime > booking.start_datetime
            ):
                tz = pytz.timezone(self.event_id.date_tz)
                start_date_tz = pytz.utc.localize(booking.start_datetime).astimezone(tz)
                end_date_tz = pytz.utc.localize(booking.stop_datetime).astimezone(tz)
                raise ValidationError(
                    _(
                        "La Sala %(room_name)s ya está reservada durante el horario: %(start_date)s - %(end_date)s",
                        room_name=booking.room_id.name,
                        start_date=start_date_tz.strftime("%d/%m/%Y %H:%M"),
                        end_date=end_date_tz.strftime("%d/%m/%Y %H:%M"),
                    )
                )

    def action_view_room_bookings(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Room Bookings",
            "view_mode": "calendar,gantt",
            "res_model": "room.booking",
            "domain": [("room_id", "=", self.room_id.id)],
            "context": {
                "initial_date": self.event_id.date_begin,
                **self.env.context,
            },
        }
