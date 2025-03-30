{
    "name": "Contacto: Personalización",  # str - required
    "version": "0.0.1",  # str
    "category": "Contactos",  # str - default: Uncategorized
    "summary": "Personalización de Contacto",  # str
    "description": """
        Se agregan nuevos campos al formulario de contacto.
    """,  # str,
    "author": "Bitmotto",  # str
    "company": "Bitmotto",  # str
    "maintainer": "Bitmotto",  # str
    "website": "https://www.bitmotto.com",
    "depends": ["base", "contacts"],  # list(str)
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/especialidad.xml",
    ],  # list(str)
    "license": "LGPL-3",  # str - default: LGPL-3
    "installable": True,  # bool - default: True
    "auto_install": False,  # bool - default: False
    "application": False,  # bool - default: False
}
