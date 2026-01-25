{
    "name": "Event Minimal Checkout",
    "version": "18.0.1.0.1",
    "category": "Website/Events",
    "summary": "Minimalist Stripe-style checkout for event registration",
    "description": """
Event Minimal Checkout
======================

Replace the standard event registration page with a minimalist checkout experience:

Features:
---------
* Stripe-inspired checkout design
* 3-step progress bar (Tickets → Attendees → Pay)
* Compact attendee form with required fields only
* Clean order summary and payment flow
* Feature flag support (?minimal=1)
* SEO-friendly with canonical tags and noindex

Technical:
----------
* Inherits website_event registration controller
* Maintains compatibility with existing event registration flow
* Client-side validation with inline error display
* Mobile-responsive design

Usage:
------
* Access via /event/<slug>/register?minimal=1
* Falls back to standard registration with ?minimal=0
""",
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "website_event",
        "website_payment",
        "payment",
        "website_sale",
        "sale",
        "event_sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/templates.xml",
        "views/event_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "event_checkout_minimal/static/src/css/checkout.css",
            "event_checkout_minimal/static/src/js/minimal_checkout.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
