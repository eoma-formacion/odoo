from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    event_id = fields.Many2one(
        'event.event',
        string='Event',
        help="Event related to this order line"
    )
    event_ticket_id = fields.Many2one(
        'event.event.ticket',
        string='Event Ticket',
        help="Specific ticket type for this registration"
    )

    @api.constrains('product_id', 'event_id', 'event_ticket_id')
    def _check_event_product_consistency(self):
        """Validate that event products have event and ticket information"""
        for line in self:
            # Check if this is an event-related line by the presence of event_ticket_id
            # This is more reliable than checking product type in Odoo v18
            if line.event_ticket_id:
                if not line.event_id:
                    raise ValidationError(
                        _('The sale order line with the product Event Registration needs an event.')
                    )
                # Validate that the ticket belongs to the event
                if line.event_ticket_id.event_id != line.event_id:
                    raise ValidationError(
                        _('The selected ticket does not belong to the specified event.')
                    )
            # Alternative check: if product_id exists but no event_ticket_id, 
            # check if it's an event product via other means
            elif line.product_id and hasattr(line.product_id, 'event_ok') and line.product_id.event_ok:
                if not line.event_id:
                    raise ValidationError(
                        _('The sale order line with the product Event Registration needs an event.')
                    )
                if not line.event_ticket_id:
                    raise ValidationError(
                        _('The sale order line with the product Event Registration needs a ticket.')
                    )

    @api.onchange('event_ticket_id')
    def _onchange_event_ticket_id(self):
        """Auto-set the event when ticket is selected"""
        if self.event_ticket_id:
            self.event_id = self.event_ticket_id.event_id
            if self.event_ticket_id.product_id:
                self.product_id = self.event_ticket_id.product_id

    @api.onchange('event_id')
    def _onchange_event_id(self):
        """Filter ticket options based on selected event"""
        if self.event_id:
            return {
                'domain': {
                    'event_ticket_id': [('event_id', '=', self.event_id.id)]
                }
            }
        return {
            'domain': {
                'event_ticket_id': []
            }
        }