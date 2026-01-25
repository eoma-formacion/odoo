# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    quoter_id = fields.Many2one(
        'sale.order',
        string='Cotización',
        help='Cotización asociada a este pago.',
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        related='quoter_id.user_id',
        store=False,
        readonly=True,
    )
