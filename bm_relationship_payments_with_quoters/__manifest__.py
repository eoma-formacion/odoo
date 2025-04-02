# -*- coding: utf-8 -*-
{
    "name": "Relationship of payments with contributions",
    "summary": "Relationship of payments with contributions module.",
    "description": """
        Relationship of payments with contributions.
    """,
    "author": "Daniel Galindez",
    "company": "Bitmotto",
    "maintainer": "Wilfred Vásquez",
    "website": "www.bitmotto.com",
    "category": "Payments",
    "version": "0.1",
    "application": False,
    "license": "OPL-1",
    "depends": ["sale", "account", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/scheduled_action.xml",
        "views/account_payment_views.xml",
        "views/sale_order_views.xml",
        "wizards/quote_balance.xml",
    ],
}
