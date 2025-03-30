from random import randint
from odoo import models, fields


class Especialidad(models.Model):
    _name = "res.partner.especialidad"
    _description = "Especialidad"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Nombre", required=True)
    color = fields.Integer(string="Color", default=_get_default_color, aggregator=False)
    partner_ids = fields.Many2many(
        "res.partner",
        column1="especialidad_id",
        column2="partner_id",
        string="Partners",
        copy=False,
    )
    active = fields.Boolean(string="Activo", default=True)
