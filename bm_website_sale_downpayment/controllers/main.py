from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSale


class EventPrepaymentController(http.Controller):

    @http.route(
        "/website/sale/prepayment/<int:order_id>",
        type="http",
        auth="public",
        website=True,
    )
    def event_prepayment(self, order_id=None, **kwargs):
        if not order_id:
            return request.redirect("/shop")  # Redirigir si no hay orden

        # Obtener la orden de venta
        sale_order = request.env["sale.order"].sudo().browse(int(order_id))
        if not sale_order.exists():
            return request.redirect("/shop")  # Redirigir si la orden no existe

        # Lógica personalizada para la orden
        action = sale_order.action_preview_sale_order()
        return request.redirect(
            action["url"] + "&downpayment=true&showPaymentModal=true"
        )


class BmWebsiteSale(WebsiteSale):
    def _check_cart_and_addresses(self, order_sudo):
        """Check whether the cart and its addresses are valid, and redirect to the appropriate page
        if not.

        :param sale.order order_sudo: The cart to check.
        :return: None if both the cart and its addresses are valid; otherwise, a redirection to the
                 appropriate page.
        """
        return request.redirect("/website/sale/prepayment/" + str(order_sudo.id))
