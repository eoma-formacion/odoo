from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_paid = fields.Monetary(compute="_compute_total_paid", string="Total Pagado")
    remaining_amount = fields.Monetary(
        compute="_compute_remaining_amount", string="Monto Restante"
    )

    payment_ids = fields.One2many(
        comodel_name="account.payment",
        inverse_name="quoter_id",
        string="Pagos",
        readonly=True,
    )

    expense = fields.Monetary(compute="_compute_expense", string="Gastos", store=True)

    fee = fields.Monetary(compute="_compute_fee", string="Honorarios", store=True)

    @api.depends(
        "order_line.product_id.property_account_income_id.code",
        "order_line.price_subtotal",
    )
    def _compute_fee(self):
        for order in self:
            order.fee = sum(
                line.price_subtotal for line in order._get_fee_order_lines()
            )

    # Acciones planificados Recalcular remaining amount
    def action_recompute_remaining_amount(self):
        """Recalcula el remaining_amount para todos los registros."""
        sale_orders = self.env["sale.order"].search([])
        sale_orders._compute_remaining_amount()

    def _get_fee_order_lines(self):
        """
        Get order lines that are fees, defined as those that are
        linked to products whose income account's code starts with '4.'.
        """

        def is_fee(line):
            return (
                line.product_id
                and line.product_id.property_account_income_id
                and line.product_id.property_account_income_id.code
                and line.product_id.property_account_income_id.code.startswith("4.")
            )

        return self.order_line.filtered(is_fee)

    @api.depends(
        "order_line.product_id.property_account_income_id.code",
        "order_line.price_subtotal",
    )
    def _compute_expense(self):
        for order in self:
            order.expense = sum(
                line.price_subtotal for line in order._get_expense_order_lines()
            )

    def _get_expense_order_lines(self):
        """
        Get order lines that are expenses, defined as those that are
        linked to products whose income account's code starts with '2.'.
        """

        def is_expense(line):
            return (
                line.product_id
                and line.product_id.property_account_income_id
                and line.product_id.property_account_income_id.code
                and line.product_id.property_account_income_id.code.startswith("2.")
            )

        return self.order_line.filtered(is_expense)

    @api.depends("payment_ids.state", "payment_ids.payment_type", "payment_ids.amount")
    def _compute_total_paid(self):
        for order in self:
            total_in = sum(
                payment.amount
                for payment in order.payment_ids.filtered(
                    lambda p: p.state in ["in_process", "paid"]
                    and p.payment_type == "inbound"
                )
            )
            total_out = sum(
                payment.amount
                for payment in order.payment_ids.filtered(
                    lambda p: p.state in ["in_process", "paid"]
                    and p.payment_type == "outbound"
                )
            )
            order.total_paid = total_in - total_out

    @api.depends("amount_total", "total_paid", "payment_ids")
    def _compute_remaining_amount(self):
        for order in self:
            order.remaining_amount = order.amount_total - order.total_paid

    def action_quote_balance(self):
        self.ensure_one()
        view = self.env.ref("bm_relationship_payments_with_quoters.view_quote_balance")
        wiz = self.env["quote.balance"].create({"quote_id": self.id})

        payments_ids = self.env["account.payment"].search([("quoter_id", "=", self.id)])
        for p in payments_ids:
            self.env["payment.quote"].create(
                {"quote_balance_id": wiz.id, "payment_id": p.id}
            )

        return {
            "name": "Balance de Presupuesto",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "quote.balance",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }
