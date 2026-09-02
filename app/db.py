import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    specs TEXT NOT NULL,
    price TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_id INTEGER,
    plan_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'awaiting_payment',
    payment_method TEXT,
    contact_note TEXT,
    connection_info TEXT,
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS action_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS support_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    contact TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
"""

SEED_PLANS = [
    (
        "Серверы для ботов и скриптов",
        "Start",
        "Отличный выбор для новичков и любителей.",
        "200 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 3 GB SSD NVMe, Базы данных MySQL: 1, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 1 шт., Защита от DDoS",
        "19 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Pro",
        "Оптимальный баланс мощности и цены.",
        "400 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 6 GB SSD NVMe, Базы данных MySQL: 2, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Защита от DDoS",
        "39 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Premium",
        "Максимальная производительность.",
        "750 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 12 GB SSD NVMe, Базы данных MySQL: 3, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "79 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Ultra",
        "Решение для требовательных пользователей.",
        "1.5 GB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 15 GB SSD NVMe, Базы данных MySQL: 5, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "119 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Elite",
        "Для профессионалов и бизнес-приложений.",
        "2 GB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 17 GB SSD NVMe, Базы данных MySQL: 6, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "159 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Start",
        "Подойдёт для портфолио или лендинга.",
        "0.9 vCPU, 300 MB RAM, 2 GB SSD NVMe, 1 поддомен, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 1 шт.",
        "29 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Pro",
        "Подойдёт для блогов, визиток и простых интернет-магазинов.",
        "0.9 vCPU, 300 MB RAM, 5 GB SSD NVMe, 1 поддомен, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 3 шт.",
        "39 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Premium",
        "Отличный выбор для агентств и бизнеса.",
        "0.9 vCPU, 400 MB RAM, 10 GB SSD NVMe, 1 поддомен, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 5 шт.",
        "69 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Boost",
        "Ускоренный хостинг для растущих проектов.",
        "Безлимит vCPU, 1024 MB RAM, 15 GB SSD NVMe, 5 поддоменов, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 1 шт.",
        "99 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Business",
        "Хостинг для малого бизнеса.",
        "Безлимит vCPU, 1024 MB RAM, 20 GB SSD NVMe, 10 поддоменов, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 3 шт.",
        "129 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Enterprise",
        "Премиум-хостинг с высокой надёжностью.",
        "Безлимит vCPU, 1024 MB RAM, 30 GB SSD NVMe, 10 поддоменов, Базы данных MySQL, SSL-сертификат Let's Encrypt, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 5 шт., Приоритетная поддержка",
        "179 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Mini",
        "Подойдёт для прокси-сервера.",
        "1 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 5 GB SSD NVMe, Всего портов: 2, Управление через Telegram-бота, Бэкапы: 3 шт., Мощная DDoS защита",
        "49 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Start",
        "Подойдёт для маленького сервера с друзьями.",
        "1.5 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 5 GB SSD NVMe, Всего портов: 2, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "59 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Standard",
        "Для средних серверов с модами и игроками.",
        "2 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 10 GB SSD NVMe, Всего портов: 4, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "99 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Premium",
        "Для серьёзных проектов и игровых сообществ.",
        "4 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz с приоритетом, 20 GB SSD NVMe, Всего портов: 6, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "209 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Ultra",
        "Отличный выбор для мини-игр и мультисерверной инфраструктуры.",
        "6 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz с высоким приоритетом, 30 GB SSD NVMe, Всего портов: 6, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "259 ₽/мес",
    ),
]


def init_db():
    db = get_db()
    db.executescript(SCHEMA)

    count = db.execute("SELECT COUNT(*) AS n FROM plans").fetchone()["n"]
    if count == 0:
        db.executemany(
            "INSERT INTO plans (category, name, description, specs, price) VALUES (?, ?, ?, ?, ?)",
            SEED_PLANS,
        )
        db.commit()

    db.execute("UPDATE plans SET is_active = 0 WHERE category = 'VPN-серверы'")

    seed_categories = {p[0] for p in SEED_PLANS}
    for category in seed_categories:
        _sync_category_plans(db, category)

    db.commit()


def _sync_category_plans(db, category):
    current_names = [p[1] for p in SEED_PLANS if p[0] == category]
    placeholders = ", ".join("?" for _ in current_names)
    db.execute(
        f"UPDATE plans SET is_active = 0 WHERE category = ? AND name NOT IN ({placeholders})",
        [category, *current_names],
    )
    existing_names = {
        row["name"]
        for row in db.execute(
            "SELECT name FROM plans WHERE category = ?", [category]
        ).fetchall()
    }
    missing_plans = [
        p for p in SEED_PLANS if p[0] == category and p[1] not in existing_names
    ]
    if missing_plans:
        db.executemany(
            "INSERT INTO plans (category, name, description, specs, price) VALUES (?, ?, ?, ?, ?)",
            missing_plans,
        )


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("База данных инициализирована.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    with app.app_context():
        init_db()
