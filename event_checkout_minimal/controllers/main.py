from odoo import http, _
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController


class EventMinimalController(WebsiteEventController):
    """
    Inherit EventController to add minimal checkout functionality
    """

    @http.route(
        ['/event/<model("event.event"):event>/register'],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def event_register(self, event, **kwargs):
        """
        Override event registration to serve minimal checkout when requested

        URL Parameters:
        - minimal=1: Show minimal checkout (default behavior)
        - minimal=0: Show standard registration page
        """
        # Check if minimal checkout is requested (default to True)
        minimal_param = request.httprequest.args.get("minimal", "1")
        is_minimal = minimal_param != "0"

        # If not minimal, use the original registration flow
        if not is_minimal:
            return super().event_register(event, **kwargs)

        # For minimal checkout, prepare our own values to avoid recursion
        values = self._prepare_minimal_event_values(event, **kwargs)

        # Render our minimal checkout template
        return request.render("event_checkout_minimal.minimal_checkout_page", values)

    def _prepare_minimal_event_values(self, event, **kwargs):
        """
        Prepare values specifically for minimal checkout (no recursion)
        """
        # Get available tickets (launched, available for sale, not expired)
        # Use sudo() to bypass access rights for ticket filtering
        available_tickets = (
            request.env["event.event.ticket"]
            .sudo()
            .search(
                [
                    ("event_id", "=", event.id),
                    ("is_launched", "=", True),
                    ("sale_available", "=", True),
                    ("is_expired", "=", False),
                ]
            )
        )

        # Prepare address information safely using sudo()
        address_info = {}
        if event.address_id:
            try:
                address_sudo = (
                    request.env["res.partner"].sudo().browse(event.address_id.id)
                )
                if address_sudo.exists():
                    address_info = {
                        "street": address_sudo.street or "",
                        "street2": address_sudo.street2 or "",
                        "city": address_sudo.city or "",
                        "state_name": (
                            address_sudo.state_id.name if address_sudo.state_id else ""
                        ),
                        "country_name": (
                            address_sudo.country_id.name
                            if address_sudo.country_id
                            else ""
                        ),
                        "zip": address_sudo.zip or "",
                    }
            except Exception:
                # If we can't access address, just use empty values
                address_info = {}

        values = {
            "event": event,
            "main_object": event,
            "range": range,
            "tickets": available_tickets,
            "minimal": True,
            "page_title": _("Checkout - %s", event.name),
            "default_first_attendee": kwargs.get("default_first_attendee", {}),
            "address_info": address_info,
        }

        # Add canonical URL for SEO
        if hasattr(event, "website_url"):
            values["canonical_url"] = event.website_url

        return values

    @http.route(
        ['/event/<model("event.event"):event>/registration/confirm'],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def event_registration_confirm(self, event, **post):
        """
        Override registration confirmation to handle minimal checkout flow
        """
        # Check if this is from minimal checkout
        is_minimal = post.get("from_minimal") == "1"

        if is_minimal:
            # Process the registration
            result = super().event_registration_confirm(event, **post)

            # If successful and there's a payment needed, redirect to payment
            if (
                hasattr(result, "location")
                and "registration/success" in result.location
            ):
                # Check if payment is required
                registration_ids = request.session.get("registration_ids", [])
                if registration_ids:
                    # Get the first registration to check for payment
                    registration = (
                        request.env["event.registration"]
                        .sudo()
                        .browse(registration_ids[0])
                    )
                    if (
                        registration
                        and registration.event_id.website_menu
                        and hasattr(registration, "payment_transaction_id")
                    ):
                        # Redirect to payment if needed
                        return request.redirect("/shop/payment")

            return result

        # Standard flow
        return super().event_registration_confirm(event, **post)

    def _process_attendees_form(self, event, form_details, **kwargs):
        """
        Process attendee form data for minimal checkout
        """
        try:
            registrations = []

            for ticket_id, attendees in form_details.items():
                ticket = request.env["event.event.ticket"].sudo().browse(int(ticket_id))

                for attendee_data in attendees:
                    # Validate required fields
                    if not attendee_data.get("name") or not attendee_data.get("email"):
                        return {
                            "error": _("Name and email are required for all attendees")
                        }

                    # Create registration
                    registration_vals = {
                        "event_id": event.id,
                        "event_ticket_id": ticket.id,
                        "name": attendee_data["name"],
                        "email": attendee_data["email"],
                        "phone": attendee_data.get("phone", ""),
                    }

                    registration = (
                        request.env["event.registration"]
                        .sudo()
                        .create(registration_vals)
                    )
                    registrations.append(registration.id)

            # Store registration IDs in session
            request.session["registration_ids"] = registrations

            return {"success": True, "registration_ids": registrations}

        except Exception as e:
            return {"error": str(e)}

    @http.route(
        ["/event/checkout/create_order"], type="json", auth="public", website=True
    )
    def create_order_from_checkout(self, event_id, attendees, billing=None):
        """
        Create sales order from minimal checkout data

        Args:
            event_id: ID of the event
            attendees: List of attendee data with ticket information
                      Format: [{'ticket_id': int, 'name': str, 'email': str, 'phone': str}, ...]
            billing: Billing information dict
                    Format: {'type': 'person'|'company', 'name': str, 'email': str, 'phone': str, 'address': str, 'nif_cif': str}

        Returns:
            dict: {'success': bool, 'order_id': int, 'payment_url': str} or error
        """
        try:
            event = request.env["event.event"].sudo().browse(int(event_id))
            if not event.exists():
                return {"success": False, "error": _("Event not found")}

            # Validate attendees data
            if not attendees:
                return {"success": False, "error": _("No attendees provided")}

            # Validate attendee data and ticket availability
            validation_result = self._validate_checkout_data(event, attendees, billing)
            if not validation_result["success"]:
                return validation_result

            # Create or find customer (use billing info if available, otherwise first attendee)
            if billing:
                partner = self._create_or_find_billing_partner(billing)
            else:
                first_attendee = attendees[0]
                partner = self._create_or_find_partner(first_attendee)

            # Create sales order
            order = self._create_sales_order(event, partner, attendees)

            # Store attendees and billing data in session for later processing
            request.session[f"checkout_attendees_{order.id}"] = attendees
            if billing:
                request.session[f"checkout_billing_{order.id}"] = billing

            # Generate order portal URL with access token and payment modal parameters
            portal_url = order.get_portal_url(
                query_string="&downpayment=true&showPaymentModal=true"
            )

            return {
                "success": True,
                "order_id": order.id,
                "portal_url": portal_url,
                "access_token": order.access_token,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_checkout_data(self, event, attendees, billing=None):
        """Validate attendee data, billing info, and ticket availability"""
        errors = {}

        # Group attendees by ticket to check availability
        ticket_counts = {}
        for i, attendee in enumerate(attendees):
            if not attendee.get("name"):
                errors[f"attendee_{i}_name"] = _("Name is required")
            if not attendee.get("email"):
                errors[f"attendee_{i}_email"] = _("Email is required")
            elif "@" not in attendee["email"]:
                errors[f"attendee_{i}_email"] = _("Valid email is required")
            if not attendee.get("phone"):
                errors[f"attendee_{i}_phone"] = _("Phone number is required")

            ticket_id = attendee.get("ticket_id")
            if not ticket_id:
                errors[f"attendee_{i}_ticket"] = _("Ticket is required")
                continue

            ticket_counts[ticket_id] = ticket_counts.get(ticket_id, 0) + 1

        # Check ticket availability
        for ticket_id, count in ticket_counts.items():
            ticket = request.env["event.event.ticket"].sudo().browse(int(ticket_id))
            if not ticket.exists():
                errors[f"ticket_{ticket_id}"] = _("Ticket not found")
                continue

            # Check seat availability if seat limits are set (seats_max > 0)
            if (
                ticket.seats_max
                and ticket.seats_max > 0
                and ticket.seats_available < count
            ):
                errors[f"ticket_{ticket_id}"] = (
                    _("Not enough tickets available. Only %d remaining.")
                    % ticket.seats_available
                )

        # Validate billing information if provided
        if billing:
            if not billing.get("name"):
                errors["billing_name"] = _("Billing name is required")
            if not billing.get("email"):
                errors["billing_email"] = _("Billing email is required")
            elif "@" not in billing["email"]:
                errors["billing_email"] = _("Valid billing email is required")
            if not billing.get("phone"):
                errors["billing_phone"] = _("Billing phone is required")
            if not billing.get("address"):
                errors["billing_address"] = _("Billing address is required")
            if not billing.get("nif_cif"):
                errors["billing_nif_cif"] = _("NIF/CIF is required")

        return {"success": len(errors) == 0, "errors": errors}

    def _create_or_find_partner(self, attendee_data):
        """Create or find partner based on attendee email"""
        Partner = request.env["res.partner"].sudo()

        # Try to find existing partner by email
        partner = Partner.search([("email", "=", attendee_data["email"])], limit=1)

        if not partner:
            # Create new partner
            partner_vals = {
                "name": attendee_data["name"],
                "email": attendee_data["email"],
                "phone": attendee_data.get("phone", ""),
                "is_company": False,
                "customer_rank": 1,
            }
            partner = Partner.create(partner_vals)

        return partner

    def _create_or_find_billing_partner(self, billing_data):
        """Create or find partner based on billing information"""
        Partner = request.env["res.partner"].sudo()

        is_company = billing_data.get("type") == "company"

        # Try to find existing partner by VAT or email
        domain = []
        if billing_data.get("nif_cif"):
            domain.append(("vat", "=", billing_data["nif_cif"]))
        elif billing_data.get("email"):
            domain.append(("email", "=", billing_data["email"]))

        partner = Partner.search(domain, limit=1) if domain else False

        if not partner:
            # Create new partner
            partner_vals = {
                "name": billing_data["name"],
                "email": billing_data["email"],
                "phone": billing_data["phone"],
                "street": billing_data.get("address", ""),
                "vat": billing_data.get("nif_cif", ""),
                "is_company": is_company,
                "customer_rank": 1,
            }
            partner = Partner.create(partner_vals)
        else:
            # Update existing partner with latest info
            update_vals = {
                "name": billing_data["name"],
                "phone": billing_data["phone"],
                "street": billing_data.get("address", ""),
            }
            if not partner.vat and billing_data.get("nif_cif"):
                update_vals["vat"] = billing_data["nif_cif"]
            partner.write(update_vals)

        return partner

    def _create_sales_order(self, event, partner, attendees):
        """Create sales order with one line per attendee"""
        SaleOrder = request.env["sale.order"].sudo()

        # Create sales order
        order_vals = {
            "partner_id": partner.id,
            "state": "draft",  # Keep as quotation
            "website_id": request.website.id,
        }
        order = SaleOrder.create(order_vals)

        # Add one line per attendee
        for attendee in attendees:
            ticket = (
                request.env["event.event.ticket"]
                .sudo()
                .browse(int(attendee["ticket_id"]))
            )
            if not ticket.product_id:
                raise ValueError(_("Ticket %s has no associated product") % ticket.name)

            # Create order line with event and ticket configuration
            line_vals = {
                "order_id": order.id,
                "product_id": ticket.product_id.id,
                "product_uom_qty": 1,
                "price_unit": ticket.price,
                "name": f"{ticket.name} - {attendee['name']}",
                "event_id": event.id,
                "event_ticket_id": ticket.id,
            }
            request.env["sale.order.line"].sudo().create(line_vals)

        return order

    @http.route("/event/checkout/validate", type="json", auth="public", website=True)
    def validate_checkout_form(self, event_id, form_data):
        """
        AJAX endpoint to validate checkout form data
        """
        try:
            event = request.env["event.event"].sudo().browse(int(event_id))

            errors = {}

            # Validate tickets and attendees
            for ticket_id, quantity in form_data.get("tickets", {}).items():
                if int(quantity) > 0:
                    ticket = (
                        request.env["event.event.ticket"].sudo().browse(int(ticket_id))
                    )

                    # Check availability if seat limits are set
                    if (
                        ticket.seats_max
                        and ticket.seats_max > 0
                        and ticket.seats_available < int(quantity)
                    ):
                        errors[f"ticket_{ticket_id}"] = _(
                            "Not enough tickets available"
                        )

            # Validate attendee data
            attendees = form_data.get("attendees", [])
            for i, attendee in enumerate(attendees):
                if not attendee.get("name"):
                    errors[f"attendee_{i}_name"] = _("Name is required")
                if not attendee.get("email"):
                    errors[f"attendee_{i}_email"] = _("Email is required")
                elif "@" not in attendee["email"]:
                    errors[f"attendee_{i}_email"] = _("Valid email is required")
                if not attendee.get("phone"):
                    errors[f"attendee_{i}_phone"] = _("Phone number is required")

            return {"success": len(errors) == 0, "errors": errors}

        except Exception as e:
            return {"success": False, "errors": {"general": str(e)}}

    @http.route(["/event/checkout/test"], type="json", auth="public", website=True)
    def test_endpoint(self):
        """Simple test endpoint to verify module is loaded"""
        return {"success": True, "message": "Event Minimal Checkout module is working"}
