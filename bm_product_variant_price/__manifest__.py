# Copyright 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Fabien Bourgeois <fabien@yaltik.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Product Variant Sale Price",
    "summary": "Allows to write fixed prices in product variants",
    "description": "Este módulo es de la versión 17, pero fue adaptado al 18",
    # "version": "18.0.1.0",
    "category": "Product Management",
    "website": "https://github.com/OCA/product-variant",
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account", "sale"],
    "data": ["views/product.xml"],
    "post_init_hook": "set_sale_price_on_variant",
}
