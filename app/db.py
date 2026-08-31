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
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    specs TEXT NOT NULL,
    price TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER,
    server_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'new',
    FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE SET NULL
);
"""

SEED_SERVERS = [
    (
        "Старт",
        "Лёгкий сервер для небольшой группы игроков.",
        "2 vCPU, 4 GB RAM, 40 GB NVMe",
        "от 990 ₽/мес",
    ),
    (
        "Стандарт",
        "Оптимальный баланс мощности и цены для активного сообщества.",
        "4 vCPU, 8 GB RAM, 80 GB NVMe",
        "от 1990 ₽/мес",
    ),
    (
        "Максимум",
        "Для крупных проектов и модов с высокой нагрузкой.",
        "8 vCPU, 16 GB RAM, 160 GB NVMe",
        "от 3990 ₽/мес",
    ),
]


def init_db():
    db = get_db()
    db.executescript(SCHEMA)

    count = db.execute("SELECT COUNT(*) AS n FROM servers").fetchone()["n"]
    if count == 0:
        db.executemany(
            "INSERT INTO servers (name, description, specs, price) VALUES (?, ?, ?, ?)",
            SEED_SERVERS,
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
