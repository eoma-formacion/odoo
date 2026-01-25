# -*- coding: utf-8 -*-

from odoo import fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        related='sale_order_id.user_id',
        store=False,
        readonly=True,
    )
