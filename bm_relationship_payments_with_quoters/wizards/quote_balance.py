# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentQuote(models.TransientModel):
    _name = "payment.quote"

    name = fields.Char(related="payment_id.name", string="Pago Nro.", readonly=True)
    quote_balance_id = fields.Many2one("quote.balance", readonly=True)
    payment_id = fields.Many2one("account.payment", string="Pagos", readonly=True)
    amount = fields.Monetary(related="payment_id.amount", string="Monto", readonly=True)
    currency_id = fields.Many2one(related="quote_balance_id.currency_id")


class QuoterBalance(models.TransientModel):
    _name = "quote.balance"

    quote_id = fields.Many2one("sale.order", "Presupuesto", readonly=True)
    currency_id = fields.Many2one(related="quote_id.currency_id")
    quote_amount = fields.Monetary(
        "Monto del Presupuesto", compute="_compute_quote_values", readonly=True
    )
    payment_ids = fields.One2many(
        "payment.quote", "quote_balance_id", string="Pagos", readonly=True
    )
    total_payments_amount = fields.Monetary(
        "Monto total de Pagos", compute="_compute_quote_values", readonly=True
    )
    balance_amount = fields.Monetary(
        "Monto restante", compute="_compute_quote_values", readonly=True
    )

    def _compute_quote_values(self):
        for rec in self:
            rec.quote_amount = rec.quote_id.amount_total
            payments_amount = 0
            for p in rec.payment_ids:
                payments_amount += p.payment_id.amount

            rec.total_payments_amount = payments_amount
            rec.balance_amount = rec.quote_amount - payments_amount
