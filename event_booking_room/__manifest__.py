{
    "name": "Enlace de eventos con Sala de Reuniones",  # str - required
    "version": "0.0.1",  # str
    "category": "Technical",  # str - default: Uncategorized
    "summary": "Enlace de eventos con Sala de Reuniones",  # str
    "description": """
        Enlace de eventos con Sala de Reuniones
    """,  # str,
    "author": "Bitmotto",  # str
    "company": "Bitmotto",  # str
    "maintainer": "Bitmotto",  # str
    "website": "https://www.bitmotto.com",
    "depends": ["base", "event", "room"],  # list(str)
    "data": ["views/event.xml", "views/room_room.xml"],  # list(str)
    "license": "LGPL-3",  # str - default: LGPL-3
    "installable": True,  # bool - default: True
    "auto_install": False,  # bool - default: False
    "application": False,  # bool - default: False
}
