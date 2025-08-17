from odoo import models, fields, api, _
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Billing information fields
    billing_type = fields.Selection([('person', 'Particular'), ('company', 'Empresa')], string='Tipo de Facturación')
    billing_name = fields.Char(string='Nombre de Facturación')
    billing_email = fields.Char(string='Email de Facturación')
    billing_phone = fields.Char(string='Teléfono de Facturación')
    billing_address = fields.Text(string='Dirección de Facturación')
    billing_nif_cif = fields.Char(string='NIF/CIF')
    billing_company_name = fields.Char(string='Razón Social')
    billing_is_company = fields.Boolean(string='Es Empresa', compute='_compute_billing_is_company', store=True)
    
    @api.depends('billing_type')
    def _compute_billing_is_company(self):
        for record in self:
            record.billing_is_company = record.billing_type == 'company'

    def action_confirm(self):
        """Override to update event registrations with attendee data"""
        res = super().action_confirm()
        
        # Update existing registrations created by standard Odoo with our attendee data
        self._update_event_registrations_with_attendee_data()
        
        return res

    def _update_event_registrations_with_attendee_data(self):
        """Update existing event registrations with attendee data from checkout"""
        for order in self:
            # Try to get attendees data from session
            attendees_session_key = f'checkout_attendees_{order.id}'
            billing_session_key = f'checkout_billing_{order.id}'
            
            if request and hasattr(request, 'session'):
                # Process attendees data
                if attendees_session_key in request.session:
                    attendees_data = request.session[attendees_session_key]
                    self._process_checkout_attendee_updates(order, attendees_data)
                    # Clean up session data
                    del request.session[attendees_session_key]
                
                # Process billing data
                if billing_session_key in request.session:
                    billing_data = request.session[billing_session_key]
                    self._process_billing_data(order, billing_data)
                    # Clean up session data
                    del request.session[billing_session_key]

    def _process_checkout_attendee_updates(self, order, attendees_data):
        """Update existing registrations with attendee data"""
        # Get existing registrations created by standard Odoo
        existing_registrations = self.env['event.registration'].search([
            ('sale_order_id', '=', order.id)
        ])
        
        # Match registrations with attendee data
        for line in order.order_line:
            if hasattr(line, 'event_id') and line.event_id and hasattr(line, 'event_ticket_id') and line.event_ticket_id:
                # Find registration for this line
                registration = existing_registrations.filtered(lambda r: r.sale_order_line_id == line)
                
                # Find corresponding attendee data
                for attendee in attendees_data[:]:  # Use slice to avoid modification issues
                    if attendee['ticket_id'] == line.event_ticket_id.id:
                        if registration:
                            # Update existing registration with attendee data
                            self._update_registration_with_attendee_data(registration, attendee)
                        attendees_data.remove(attendee)
                        break

    def _update_registration_with_attendee_data(self, registration, attendee_data):
        """Update a registration with specific attendee data"""
        # Get or create partner for the attendee
        partner = self._get_or_create_attendee_partner(attendee_data)
        
        # Update registration with attendee-specific information
        registration.write({
            'partner_id': partner.id,
            'name': attendee_data['name'],
            'email': attendee_data['email'],
            'phone': attendee_data.get('phone', ''),
        })

    def _get_or_create_attendee_partner(self, attendee_data):
        """Get existing partner or create new one for attendee"""
        Partner = self.env['res.partner']
        
        # Try to find existing partner
        partner = Partner.search([
            ('email', '=', attendee_data['email'])
        ], limit=1)
        
        if not partner:
            # Create new partner
            partner_vals = {
                'name': attendee_data['name'],
                'email': attendee_data['email'],
                'phone': attendee_data.get('phone', ''),
                'is_company': False,
                'customer_rank': 1,
            }
            partner = Partner.create(partner_vals)
        
        return partner
    
    def _process_billing_data(self, order, billing_data):
        """Process billing information and update order"""
        if not billing_data:
            return
            
        # Update sale order with billing information
        billing_vals = {
            'billing_type': billing_data.get('type', 'person'),
            'billing_name': billing_data.get('name', ''),
            'billing_email': billing_data.get('email', ''),
            'billing_phone': billing_data.get('phone', ''),
            'billing_address': billing_data.get('address', ''),
            'billing_nif_cif': billing_data.get('nif_cif', ''),
        }
        
        # For companies, also store company name
        if billing_data.get('type') == 'company':
            billing_vals['billing_company_name'] = billing_data.get('name', '')
            
        order.write(billing_vals)
        
        # Update or create billing partner
        self._update_billing_partner(order, billing_data)
    
    def _update_billing_partner(self, order, billing_data):
        """Update order partner with billing information or create invoice partner"""
        Partner = self.env['res.partner']
        
        # Check if we should update the main partner or create a separate invoice partner
        is_company = billing_data.get('type') == 'company'
        
        # Create partner values
        partner_vals = {
            'name': billing_data.get('name', ''),
            'email': billing_data.get('email', ''),
            'phone': billing_data.get('phone', ''),
            'street': billing_data.get('address', ''),
            'is_company': is_company,
            'customer_rank': 1,
            'vat': billing_data.get('nif_cif', ''),
        }
        
        # Try to find existing partner with same VAT/email
        domain = []
        if billing_data.get('nif_cif'):
            domain.append(('vat', '=', billing_data.get('nif_cif')))
        elif billing_data.get('email'):
            domain.append(('email', '=', billing_data.get('email')))
            
        existing_partner = Partner.search(domain, limit=1) if domain else False
        
        if existing_partner:
            # Update existing partner
            existing_partner.write(partner_vals)
            billing_partner = existing_partner
        else:
            # Create new partner
            billing_partner = Partner.create(partner_vals)
        
        # Update order with billing partner
        if order.partner_id != billing_partner:
            order.write({
                'partner_invoice_id': billing_partner.id,
            })