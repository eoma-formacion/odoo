from odoo import http
from odoo.http import request


class EventPrepaymentController(http.Controller):

    @http.route(
        "/event/prepayment/<int:order_id>", type="http", auth="public", website=True
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
        return request.redirect(action["url"])
