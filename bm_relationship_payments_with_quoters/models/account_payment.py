# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    quoter_id = fields.Many2one(
        'sale.order',
        string='Cotización',
        help='Cotización asociada a este pago.',
    )
