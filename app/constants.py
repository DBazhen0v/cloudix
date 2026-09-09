import math

PLAN_CATEGORY_ORDER = [
    "Серверы для ботов и скриптов",
    "Веб-хостинг",
    "Minecraft-сервера",
]

# Geographic crop the hero map projects onto (an equirectangular projection
# with a standard parallel at the crop's mid-latitude - the same formula the
# template's JS uses for every point, line and country border, so nothing on
# the map is ever hand-positioned). Covers the Netherlands/Germany/Poland/
# Norway cluster with some surrounding context; view height is derived from
# the bounds so the SVG viewBox and the projection always stay in sync.
HERO_MAP_BOUNDS = {"lon_min": -10, "lon_max": 28, "lat_min": 44, "lat_max": 63}
HERO_MAP_VIEW_WIDTH = 1000
HERO_MAP_VIEW_HEIGHT = round(
    HERO_MAP_VIEW_WIDTH
    * (HERO_MAP_BOUNDS["lat_max"] - HERO_MAP_BOUNDS["lat_min"])
    / (
        (HERO_MAP_BOUNDS["lon_max"] - HERO_MAP_BOUNDS["lon_min"])
        * math.cos(math.radians((HERO_MAP_BOUNDS["lat_min"] + HERO_MAP_BOUNDS["lat_max"]) / 2))
    ),
    1,
)

# Hero network map: one entry per datacenter/city. Position on the map is
# never hand-placed - lat/lon are real geographic coordinates, and the
# template's projection function is the only thing that turns them into
# screen positions. Adding a new location is just a new dict here.
SERVER_LOCATIONS = [
    {
        "id": "ams",
        "city": "Amsterdam",
        "country": "Нидерланды",
        "flag": "nl",
        "lat": 52.3676,
        "lon": 4.9041,
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
        "lat": 50.1109,
        "lon": 8.6821,
        "status": "soon",
    },
    {
        "id": "waw",
        "city": "Warsaw",
        "country": "Польша",
        "flag": "pl",
        "lat": 52.2297,
        "lon": 21.0122,
        "status": "soon",
    },
    {
        "id": "osl",
        "city": "Oslo",
        "country": "Норвегия",
        "flag": "no",
        "lat": 59.9139,
        "lon": 10.7522,
        "status": "soon",
    },
    {
        "id": "nyc",
        "city": "New York",
        "country": "США",
        "flag": "us",
        "lat": 40.7128,
        "lon": -74.0060,
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
