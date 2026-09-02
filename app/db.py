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
        "Стандарт",
        "Для одного лёгкого бота или скрипта.",
        "1 vCPU, 1 GB RAM, 10 GB NVMe",
        "249 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Стандарт+",
        "Несколько ботов или скрипт с базой данных.",
        "2 vCPU, 2 GB RAM, 20 GB NVMe",
        "499 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Max",
        "Много ботов и высоконагруженные скрипты.",
        "4 vCPU, 4 GB RAM, 40 GB NVMe",
        "699 ₽/мес",
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
        "Стандарт",
        "Небольшая группа игроков, ванильный сервер.",
        "2 vCPU, 4 GB RAM, 40 GB NVMe",
        "249 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "Стандарт+",
        "Активное сообщество, моды и плагины.",
        "4 vCPU, 8 GB RAM, 80 GB NVMe",
        "499 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "Max",
        "Крупный проект с высокой нагрузкой.",
        "8 vCPU, 16 GB RAM, 160 GB NVMe",
        "699 ₽/мес",
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

    current_web_names = [p[1] for p in SEED_PLANS if p[0] == "Веб-хостинг"]
    placeholders = ", ".join("?" for _ in current_web_names)
    db.execute(
        f"UPDATE plans SET is_active = 0 WHERE category = 'Веб-хостинг' AND name NOT IN ({placeholders})",
        current_web_names,
    )
    existing_web_names = {
        row["name"]
        for row in db.execute(
            "SELECT name FROM plans WHERE category = 'Веб-хостинг'"
        ).fetchall()
    }
    missing_web_plans = [
        p for p in SEED_PLANS if p[0] == "Веб-хостинг" and p[1] not in existing_web_names
    ]
    if missing_web_plans:
        db.executemany(
            "INSERT INTO plans (category, name, description, specs, price) VALUES (?, ?, ?, ?, ?)",
            missing_web_plans,
        )

    db.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("База данных инициализирована.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    with app.app_context():
        init_db()
