PLAN_CATEGORY_ORDER = [
    "Серверы для ботов и скриптов",
    "Веб-хостинг",
    "Minecraft-сервера",
]

# Hero network map: one entry per datacenter/city. Adding a new location is
# just a new dict here - the map, its lines and the info card are all
# generated from this list, nothing else needs to change.
SERVER_LOCATIONS = [
    {
        "id": "ams",
        "city": "Amsterdam",
        "country": "Нидерланды",
        "flag": "nl",
        "x": 44,
        "y": 49,
        "status": "online",
        "ping": "8 ms",
        "uptime": "99.98%",
        "network": "1 Gbps",
        "storage": "NVMe",
    },
    {
        "id": "fra",
        "city": "Frankfurt",
        "country": "Германия",
        "flag": "de",
        "x": 49,
        "y": 59,
        "status": "soon",
    },
    {
        "id": "waw",
        "city": "Warsaw",
        "country": "Польша",
        "flag": "pl",
        "x": 77,
        "y": 53,
        "status": "soon",
    },
    {
        "id": "osl",
        "city": "Oslo",
        "country": "Норвегия",
        "flag": "no",
        "x": 60,
        "y": 27,
        "status": "soon",
    },
    {
        "id": "nyc",
        "city": "New York",
        "country": "США",
        "flag": "us",
        "x": 8,
        "y": 35,
        "status": "soon",
    },
]

# Which locations get a connecting line drawn between them (pairs of ids).
SERVER_LINKS = [
    ("ams", "fra"),
    ("ams", "waw"),
    ("ams", "osl"),
    ("ams", "nyc"),
    ("fra", "waw"),
]

PAYMENT_METHODS = {
    "card": "Банковская карта",
    "crypto": "Криптовалюта",
    "sbp": "СБП / перевод",
}

ACTIONS = {
    "reboot": "Перезагрузка",
    "renew": "Продление",
    "change_plan": "Смена тарифа",
}
