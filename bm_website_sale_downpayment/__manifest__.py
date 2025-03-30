{
    "name": "Anticipo en Website Sale",  # str - required
    "version": "0.0.1",  # str
    "category": "Technical",  # str - default: Uncategorized
    "summary": "Anticipo en Website Sale",  # str
    "description": """
        Creación de un botón que permite realizar un anticipo en una orden de venta en Odoo.
    """,  # str,
    "author": "Bitmotto",  # str
    "company": "Bitmotto",  # str
    "maintainer": "Bitmotto",  # str
    "website": "https://www.bitmotto.com",
    "depends": ["base", "website_sale"],  # list(str)
    "data": [
        "views/cart_templates.xml",
    ],  # list(str)
    "license": "LGPL-3",  # str - default: LGPL-3
    "installable": True,  # bool - default: True
    "auto_install": False,  # bool - default: False
    "application": False,  # bool - default: False
}
