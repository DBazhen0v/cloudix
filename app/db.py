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
        "Стандарт",
        "Для одного сайта-визитки.",
        "1 vCPU, 2 GB RAM, 20 GB NVMe",
        "249 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Стандарт+",
        "Для сайта с базой данных и умеренной посещаемостью.",
        "2 vCPU, 4 GB RAM, 40 GB NVMe",
        "499 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Max",
        "Для нескольких проектов или высоконагруженного сайта.",
        "4 vCPU, 8 GB RAM, 80 GB NVMe",
        "699 ₽/мес",
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


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("База данных инициализирована.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    with app.app_context():
        init_db()
