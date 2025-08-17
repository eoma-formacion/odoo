/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Event Minimal Checkout Interactive Widget
publicWidget.registry.MinimalCheckout = publicWidget.Widget.extend({
    selector: '.minimal-checkout-wrapper',
    events: {
        'click .qty-btn': '_onQuantityButtonClick',
        'input .qty-input': '_onQuantityInputChange',
        'click #tickets-next': '_onTicketsNext',
        'click #attendees-back': '_onAttendeesBack',
        'click #attendees-next': '_onAttendeesNext',
        'click #billing-back': '_onBillingBack',
        'change input[name="billing_type"]': '_onBillingTypeChange',
        'submit #minimal_registration_form': '_onFormSubmit',
    },

    /**
     * @override
     */
    start: function () {
        this.currentStep = 1;
        this.selectedTickets = {};
        this.totalAmount = 0;
        this.currencySymbol = '€'; // Euro symbol for Spain
        
        this._updateOrderSummary();
        this._updateProgressBar();
        this._updateContinueButton(); // Initialize button state
        
        return this._super.apply(this, arguments);
    },

    // Quantity Control Handlers
    _onQuantityButtonClick: function (ev) {
        ev.preventDefault();
        const button = ev.currentTarget;
        const ticketId = button.dataset.ticketId;
        const isPlus = button.classList.contains('qty-plus');
        const input = this.el.querySelector(`input[data-ticket-id="${ticketId}"]`);
        
        let currentValue = parseInt(input.value) || 0;
        const max = parseInt(input.getAttribute('max')) || 10;
        
        if (isPlus && currentValue < max) {
            currentValue++;
        } else if (!isPlus && currentValue > 0) {
            currentValue--;
        } else if (isPlus && currentValue >= max) {
            // Show error when trying to exceed seat limit
            this._showError(`No hay más entradas disponibles. Solo quedan ${max} asientos.`);
            return;
        }
        
        input.value = currentValue;
        this._updateTicketSelection(ticketId, currentValue);
    },

    _onQuantityInputChange: function (ev) {
        const input = ev.currentTarget;
        const ticketId = input.dataset.ticketId;
        const max = parseInt(input.getAttribute('max')) || 10;
        const requestedQuantity = parseInt(input.value) || 0;
        const quantity = Math.max(0, Math.min(requestedQuantity, max));
        
        // Show error if user tried to enter more than available
        if (requestedQuantity > max && max < 10) { // max < 10 means it's seat-limited
            this._showError(`No hay más entradas disponibles. Solo quedan ${max} asientos.`);
        }
        
        input.value = quantity; // Ensure input shows correct value
        this._updateTicketSelection(ticketId, quantity);
    },

    _updateTicketSelection: function (ticketId, quantity) {
        const ticketRow = this.el.querySelector(`[data-ticket-id="${ticketId}"]`);
        const ticketName = ticketRow.querySelector('.ticket-name').textContent.trim();
        const priceElement = ticketRow.querySelector('.ticket-price span');
        let ticketPrice = 0;
        
        // Extract price from the element (handle Spanish Euro format)
        if (priceElement) {
            const priceText = priceElement.textContent.trim();
            // Convert Spanish format (123,45 €) to JavaScript float
            // Remove currency symbol and convert comma to period for parseFloat
            ticketPrice = parseFloat(priceText.replace('€', '').replace(',', '.').trim()) || 0;
        }

        if (quantity > 0) {
            this.selectedTickets[ticketId] = {
                id: ticketId,
                name: ticketName,
                price: ticketPrice,
                quantity: quantity,
                subtotal: ticketPrice * quantity
            };
        } else {
            delete this.selectedTickets[ticketId];
        }

        this._updateOrderSummary();
        this._updateContinueButton();
    },

    _updateOrderSummary: function () {
        const orderItemsEl = this.el.querySelector('#order-summary');
        const totalAmountEls = this.el.querySelectorAll('.total-amount');
        
        // Calculate total
        this.totalAmount = Object.values(this.selectedTickets).reduce((sum, ticket) => sum + ticket.subtotal, 0);
        
        // Update order items display
        if (Object.keys(this.selectedTickets).length === 0) {
            orderItemsEl.innerHTML = '<div class="empty-cart">No hay entradas seleccionadas</div>';
        } else {
            const itemsHtml = Object.values(this.selectedTickets).map(ticket => `
                <div class="order-item">
                    <div class="item-name">${ticket.name}</div>
                    <div class="item-details">
                        <span class="item-quantity">Cantidad: ${ticket.quantity}</span>
                        <span class="item-price">${this._formatPrice(ticket.subtotal)}</span>
                    </div>
                </div>
            `).join('');
            
            orderItemsEl.innerHTML = itemsHtml;
        }
        
        // Update all total amount displays
        const formattedTotal = this._formatPrice(this.totalAmount);
        totalAmountEls.forEach(el => {
            el.textContent = formattedTotal;
        });
    },

    _formatPrice: function (amount) {
        // Spanish currency formatting - Euro symbol after amount with comma as decimal separator
        return amount.toFixed(2).replace('.', ',') + ' ' + this.currencySymbol;
    },

    // Step Navigation
    _onTicketsNext: function (ev) {
        ev.preventDefault();
        if (this._validateTicketsStep()) {
            this._goToStep(2);
            this._generateAttendeeFields();
        }
    },

    _onAttendeesBack: function (ev) {
        ev.preventDefault();
        this._goToStep(1);
    },

    _onAttendeesNext: function (ev) {
        ev.preventDefault();
        if (this._validateAttendeesStep()) {
            this._goToStep(3);
        }
    },

    _onBillingBack: function (ev) {
        ev.preventDefault();
        this._goToStep(2);
    },

    _onBillingTypeChange: function (ev) {
        const isCompany = ev.currentTarget.value === 'company';
        const personFields = this.el.querySelector('.person-fields');
        const companyFields = this.el.querySelector('.company-fields');
        
        if (isCompany) {
            personFields.style.display = 'none';
            companyFields.style.display = 'block';
            // Clear person field requirements
            this._toggleFieldRequirements(personFields, false);
            this._toggleFieldRequirements(companyFields, true);
        } else {
            personFields.style.display = 'block';
            companyFields.style.display = 'none';
            // Set field requirements
            this._toggleFieldRequirements(personFields, true);
            this._toggleFieldRequirements(companyFields, false);
        }
    },

    _goToStep: function (stepNumber) {
        // Hide all step panels
        this.el.querySelectorAll('.step-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Show target step panel
        const targetPanel = this.el.querySelector(`.step-panel[data-step="${stepNumber}"]`);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }
        
        this.currentStep = stepNumber;
        this._updateProgressBar();
    },

    _updateProgressBar: function () {
        this.el.querySelectorAll('.progress-step').forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNum < this.currentStep) {
                step.classList.add('completed');
            } else if (stepNum === this.currentStep) {
                step.classList.add('active');
            }
        });
        
        // Update progress lines (2 lines now for 3 steps)
        this.el.querySelectorAll('.progress-line').forEach((line, index) => {
            if (index === 0) {
                // First line: completed when step 2 or 3
                line.classList.toggle('completed', this.currentStep >= 2);
            } else if (index === 1) {
                // Second line: completed when step 3
                line.classList.toggle('completed', this.currentStep === 3);
            }
        });
    },

    // Update Continue Button State
    _updateContinueButton: function () {
        const totalTickets = Object.values(this.selectedTickets).reduce((sum, ticket) => sum + ticket.quantity, 0);
        const nextButton = this.el.querySelector('#tickets-next');
        
        if (totalTickets > 0) {
            nextButton.disabled = false;
            nextButton.classList.remove('disabled');
        } else {
            nextButton.disabled = true;
            nextButton.classList.add('disabled');
        }
    },

    // Validation
    _validateTicketsStep: function () {
        const hasTickets = Object.keys(this.selectedTickets).length > 0;
        
        if (hasTickets) {
            return true;
        } else {
            this._showError('Por favor selecciona al menos una entrada.');
            return false;
        }
    },

    _validateAttendeesStep: function () {
        const attendeeForms = this.el.querySelectorAll('.attendee-form');
        let isValid = true;
        
        attendeeForms.forEach(form => {
            const nameInput = form.querySelector('input[name$="[name]"]');
            const emailInput = form.querySelector('input[name$="[email]"]');
            const phoneInput = form.querySelector('input[name$="[phone]"]');
            
            // Clear previous errors
            this._clearFieldError(nameInput);
            this._clearFieldError(emailInput);
            this._clearFieldError(phoneInput);
            
            if (!nameInput.value.trim()) {
                this._showFieldError(nameInput, 'El nombre es obligatorio');
                isValid = false;
            }
            
            if (!emailInput.value.trim()) {
                this._showFieldError(emailInput, 'El email es obligatorio');
                isValid = false;
            } else if (!this._isValidEmail(emailInput.value.trim())) {
                this._showFieldError(emailInput, 'Por favor introduce un email válido');
                isValid = false;
            }
            
            if (!phoneInput.value.trim()) {
                this._showFieldError(phoneInput, 'El número de teléfono es obligatorio');
                isValid = false;
            }
        });
        
        return isValid;
    },

    _validateBillingStep: function () {
        const billingType = this.el.querySelector('input[name="billing_type"]:checked').value;
        const fieldsContainer = billingType === 'company' ? '.company-fields' : '.person-fields';
        const fields = this.el.querySelectorAll(`${fieldsContainer} input[required], ${fieldsContainer} textarea[required]`);
        let isValid = true;
        
        fields.forEach(field => {
            // Clear previous errors
            this._clearFieldError(field);
            
            if (!field.value.trim()) {
                this._showFieldError(field, 'Este campo es obligatorio');
                isValid = false;
            } else if (field.type === 'email' && !this._isValidEmail(field.value.trim())) {
                this._showFieldError(field, 'Por favor introduce un email válido');
                isValid = false;
            } else if ((field.name === 'billing_nif' || field.name === 'billing_cif') && !this._isValidNifCif(field.value.trim(), billingType)) {
                const errorMsg = billingType === 'person' ? 'Formato de NIF inválido (ej: 12345678A)' : 'Formato de CIF inválido (ej: A12345678)';
                this._showFieldError(field, errorMsg);
                isValid = false;
            }
        });
        
        return isValid;
    },

    _toggleFieldRequirements: function (container, required) {
        const fields = container.querySelectorAll('input, textarea');
        fields.forEach(field => {
            if (required) {
                field.setAttribute('required', 'required');
            } else {
                field.removeAttribute('required');
                field.value = ''; // Clear the field
            }
        });
    },

    _isValidNifCif: function (value, type) {
        if (type === 'person') {
            // NIF validation: 8 digits + 1 letter
            return /^[0-9]{8}[A-Za-z]$/.test(value);
        } else {
            // CIF validation: 1 letter + 8 digits OR 1 letter + 7 digits + 1 letter/digit
            return /^[A-Za-z][0-9]{7}[0-9A-Za-z]$/.test(value);
        }
    },

    _generateAttendeeFields: function () {
        const container = this.el.querySelector('#attendee-forms');
        let formHtml = '';
        
        Object.values(this.selectedTickets).forEach(ticket => {
            for (let i = 0; i < ticket.quantity; i++) {
                const fieldIndex = `${ticket.id}_${i}`;
                formHtml += `
                    <div class="attendee-form" data-ticket-id="${ticket.id}" data-index="${i}">
                        <h4>${ticket.name} - Asistente ${i + 1}</h4>
                        <div class="form-group">
                            <label for="name_${fieldIndex}">Nombre Completo *</label>
                            <input type="text" 
                                   id="name_${fieldIndex}" 
                                   name="attendee_${fieldIndex}[name]" 
                                   class="form-control" 
                                   required>
                        </div>
                        <div class="form-group">
                            <label for="email_${fieldIndex}">Dirección de Email *</label>
                            <input type="email" 
                                   id="email_${fieldIndex}" 
                                   name="attendee_${fieldIndex}[email]" 
                                   class="form-control" 
                                   required>
                        </div>
                        <div class="form-group">
                            <label for="phone_${fieldIndex}">Número de Teléfono *</label>
                            <input type="tel" 
                                   id="phone_${fieldIndex}" 
                                   name="attendee_${fieldIndex}[phone]" 
                                   class="form-control" 
                                   required>
                        </div>
                    </div>
                `;
            }
        });
        
        container.innerHTML = formHtml;
    },

    // Form Submission
    _onFormSubmit: function (ev) {
        ev.preventDefault(); // Always prevent default form submission
        
        if (this.currentStep !== 3) {
            return false;
        }
        
        // Validate billing information
        if (!this._validateBillingStep()) {
            return false;
        }
        
        // Validate attendees one more time
        if (!this._validateAttendeesStep()) {
            return false;
        }
        
        // Show loading state
        const submitButton = this.el.querySelector('#billing-submit');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Procesando...';
        
        // Create order via AJAX
        this._createOrderAjax();
        
        return false;
    },

    _createOrderAjax: function () {
        // Get event ID from the current URL or form
        const eventId = this._getEventId();
        if (!eventId) {
            this._showError('No se puede identificar el evento. Por favor actualiza e inténtalo de nuevo.');
            this._resetSubmitButton();
            return;
        }
        
        // Prepare attendees data
        const attendeesData = this._collectAttendeesData();
        if (!attendeesData.length) {
            this._showError('No se encontraron datos de asistentes. Por favor actualiza e inténtalo de nuevo.');
            this._resetSubmitButton();
            return;
        }
        
        // Prepare billing data
        const billingData = this._collectBillingData();
        if (!billingData) {
            this._showError('No se encontraron datos de facturación. Por favor actualiza e inténtalo de nuevo.');
            this._resetSubmitButton();
            return;
        }
        
        // Make AJAX call to create order
        fetch('/event/checkout/create_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    event_id: eventId,
                    attendees: attendeesData,
                    billing: billingData
                }
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.result && data.result.success) {
                // Redirect to order portal page
                window.location.href = data.result.portal_url;
            } else {
                // Show error
                const errorMsg = data.result?.error || 'Se produjo un error al procesar tu pedido.';
                this._showError(errorMsg);
                this._resetSubmitButton();
            }
        })
        .catch(error => {
            console.error('Order creation error:', error);
            this._showError('Error de conexión. Por favor verifica tu conexión e inténtalo de nuevo.');
            this._resetSubmitButton();
        });
    },
    
    _collectAttendeesData: function () {
        const attendeesData = [];
        const attendeeForms = this.el.querySelectorAll('.attendee-form');
        
        attendeeForms.forEach(form => {
            const ticketId = form.dataset.ticketId;
            const nameInput = form.querySelector('input[name$="[name]"]');
            const emailInput = form.querySelector('input[name$="[email]"]');
            const phoneInput = form.querySelector('input[name$="[phone]"]');
            
            if (nameInput && emailInput && phoneInput && 
                nameInput.value.trim() && emailInput.value.trim() && phoneInput.value.trim()) {
                attendeesData.push({
                    ticket_id: parseInt(ticketId),
                    name: nameInput.value.trim(),
                    email: emailInput.value.trim(),
                    phone: phoneInput.value.trim()
                });
            }
        });
        
        return attendeesData;
    },
    
    _collectBillingData: function () {
        const billingType = this.el.querySelector('input[name="billing_type"]:checked')?.value;
        if (!billingType) return null;
        
        const isCompany = billingType === 'company';
        const prefix = isCompany ? 'billing_company_' : 'billing_';
        const suffix = isCompany ? '' : '';
        
        const billingData = {
            type: billingType,
            name: this.el.querySelector(`input[name="${prefix}name${suffix}"]`)?.value?.trim() || '',
            email: this.el.querySelector(`input[name="${prefix}email${suffix}"]`)?.value?.trim() || '',
            phone: this.el.querySelector(`input[name="${prefix}phone${suffix}"]`)?.value?.trim() || '',
            address: this.el.querySelector(`textarea[name="${prefix}address${suffix}"]`)?.value?.trim() || '',
            nif_cif: this.el.querySelector(`input[name="${isCompany ? 'billing_cif' : 'billing_nif'}"]`)?.value?.trim() || ''
        };
        
        // Validate that all required fields are present
        if (!billingData.name || !billingData.email || !billingData.phone || !billingData.address || !billingData.nif_cif) {
            return null;
        }
        
        return billingData;
    },
    
    _getEventId: function () {
        // Try to extract event ID from form action or URL
        const form = this.el.querySelector('#minimal_registration_form');
        if (form && form.action) {
            const match = form.action.match(/\/event\/([^\/]+)\/registration/);
            if (match) {
                // This is a slug, we need the actual event ID
                // For now, let's try to get it from a data attribute or similar
                return this._extractEventIdFromSlug(match[1]);
            }
        }
        
        // Try to get from URL
        const currentUrl = window.location.pathname;
        const urlMatch = currentUrl.match(/\/event\/([^\/]+)\//);
        if (urlMatch) {
            return this._extractEventIdFromSlug(urlMatch[1]);
        }
        
        // Try to get from a data attribute on the wrapper
        const eventIdAttr = this.el.dataset.eventId;
        if (eventIdAttr) {
            return parseInt(eventIdAttr);
        }
        
        return null;
    },
    
    _extractEventIdFromSlug: function (slug) {
        // In Odoo, slugs typically end with -ID, extract the ID part
        const match = slug.match(/-(\d+)$/);
        return match ? parseInt(match[1]) : null;
    },
    
    _resetSubmitButton: function () {
        const submitButton = this.el.querySelector('#billing-submit');
        submitButton.disabled = false;
        submitButton.innerHTML = 'Completar Registro <i class="fa fa-arrow-right"></i>';
    },

    // Utility methods
    _isValidEmail: function (email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    _showError: function (message) {
        // Remove existing error messages
        const existingErrors = this.el.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());
        
        // Create error div
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message alert alert-danger mt-2';
        errorDiv.textContent = message;
        errorDiv.style.margin = '1rem 0';
        errorDiv.style.padding = '0.75rem';
        errorDiv.style.borderRadius = '0.5rem';
        
        // Find the best place to insert the error - try multiple strategies
        let insertLocation = null;
        
        // Strategy 1: Current step panel with step-actions
        const currentStepPanel = this.el.querySelector('.step-panel.active');
        if (currentStepPanel) {
            const stepActions = currentStepPanel.querySelector('.step-actions');
            if (stepActions && stepActions.parentNode === currentStepPanel) {
                try {
                    currentStepPanel.insertBefore(errorDiv, stepActions);
                    insertLocation = 'step-panel-before-actions';
                } catch (e) {
                    console.warn('Failed to insert before step-actions:', e);
                }
            }
            
            // Strategy 2: Just append to current step panel
            if (!insertLocation) {
                try {
                    currentStepPanel.appendChild(errorDiv);
                    insertLocation = 'step-panel-append';
                } catch (e) {
                    console.warn('Failed to append to step-panel:', e);
                }
            }
        }
        
        // Strategy 3: Insert after step content
        if (!insertLocation) {
            const stepContent = this.el.querySelector('.step-content');
            if (stepContent) {
                try {
                    stepContent.appendChild(errorDiv);
                    insertLocation = 'step-content-append';
                } catch (e) {
                    console.warn('Failed to append to step-content:', e);
                }
            }
        }
        
        // Strategy 4: Main wrapper fallback
        if (!insertLocation) {
            try {
                this.el.appendChild(errorDiv);
                insertLocation = 'main-wrapper-append';
            } catch (e) {
                console.error('Failed all error insertion strategies:', e);
                // Last resort: use alert
                alert(message);
                return;
            }
        }
        
        console.log('Error message inserted using strategy:', insertLocation);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    },

    _showFieldError: function (field, message) {
        field.classList.add('is-invalid');
        
        // Remove existing error
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error
        const errorSpan = document.createElement('span');
        errorSpan.className = 'field-error text-danger small';
        errorSpan.textContent = message;
        field.parentNode.appendChild(errorSpan);
    },

    _clearFieldError: function (field) {
        field.classList.remove('is-invalid');
        const error = field.parentNode.querySelector('.field-error');
        if (error) {
            error.remove();
        }
    },
});

// Additional CSS for form validation states
const additionalCSS = `
.form-control.is-invalid {
    border-color: var(--error-color);
    box-shadow: 0 0 0 3px rgba(240, 81, 81, 0.1);
}

.field-error {
    display: block;
    margin-top: 0.25rem;
}

.error-message {
    border-radius: var(--border-radius);
    padding: 0.75rem;
    margin: 1rem 0;
}

.btn-next.disabled, .btn-primary:disabled, .btn-next:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
    background: var(--text-secondary) !important;
}

.btn-next.disabled:hover, .btn-primary:disabled:hover, .btn-next:disabled:hover {
    background: var(--text-secondary) !important;
    transform: none;
    box-shadow: var(--shadow-button);
}

/* Loading spinner animation */
.fa-spin {
    animation: fa-spin 1s infinite linear;
}

@keyframes fa-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// Inject additional CSS
if (!document.querySelector('#minimal-checkout-validation-css')) {
    const style = document.createElement('style');
    style.id = 'minimal-checkout-validation-css';
    style.textContent = additionalCSS;
    document.head.appendChild(style);
}

console.log('Event Minimal Checkout: JavaScript module loaded successfully');