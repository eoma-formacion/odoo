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
        self.create_partner_for_event_registration(order_sudo)
        return request.redirect("/website/sale/prepayment/" + str(order_sudo.id))

    def create_partner_for_event_registration(self, order_sudo):
        """Create a new partner from the given order.

        :param sale.order order_sudo: The order from which to create the partner.
        :return: The newly created partner.
        :rtype: res.partner
        """
        country = request.env["res.country"].search([("code", "=", "ES")], limit=1)
        registrations = (
            request.env["event.registration"]
            .sudo()
            .search([("sale_order_id", "in", order_sudo.ids)])
        )
        main_partner = None
        for register in registrations:
            partner = (
                request.env["res.partner"]
                .sudo()
                .search([("email", "=", register.email)], limit=1)
            )
            # If not partner, create one
            if not partner:
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": register.name,
                            "email": register.email,
                            "phone": register.phone,
                            "country_id": country.id,
                        }
                    )
                )
            if main_partner is None:
                main_partner = partner

            register.partner_id = main_partner.id

        order_sudo.partner_id = main_partner.id
