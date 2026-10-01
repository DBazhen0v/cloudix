from pathlib import Path

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .dburl import get_database_url
from .models import Plan

engine = None
Session = None


def get_db():
    return Session()


SEED_PLANS = [
    (
        "Серверы для ботов и скриптов",
        "Start",
        "Отличный выбор для новичков и любителей.",
        "200 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 3 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 1 шт., Защита от DDoS",
        "19 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Pro",
        "Оптимальный баланс мощности и цены.",
        "400 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 6 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Защита от DDoS",
        "29 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Premium",
        "Максимальная производительность.",
        "750 MB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 12 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "59 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Ultra",
        "Решение для требовательных пользователей.",
        "1.5 GB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 15 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "99 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Elite",
        "Для профессионалов и бизнес-приложений.",
        "2 GB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 17 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "129 ₽/мес",
    ),
    (
        "Серверы для ботов и скриптов",
        "Titan",
        "Максимум ресурсов и гибкости.",
        "3 GB RAM DDR3-DDR5, Безлимит vCPU @ 3.1-5.4 GHz, 24 GB SSD NVMe, Управление через Telegram-бота, 1-10 Gbit/s Network, Бэкапы: 5 шт., Приоритетная поддержка, Защита от DDoS",
        "179 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Start",
        "Подойдёт для портфолио или лендинга.",
        "0.9 vCPU, 300 MB RAM, 2 GB SSD NVMe, 1 поддомен, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 1 шт.",
        "19 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Pro",
        "Подойдёт для блогов, визиток и простых интернет-магазинов.",
        "0.9 vCPU, 300 MB RAM, 5 GB SSD NVMe, 1 поддомен, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 3 шт.",
        "29 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Premium",
        "Отличный выбор для агентств и бизнеса.",
        "0.9 vCPU, 400 MB RAM, 10 GB SSD NVMe, 1 поддомен, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 5 шт.",
        "49 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Boost",
        "Ускоренный хостинг для растущих проектов.",
        "Безлимит vCPU, 1024 MB RAM, 15 GB SSD NVMe, 5 поддоменов, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 1 шт.",
        "79 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Business",
        "Хостинг для малого бизнеса.",
        "Безлимит vCPU, 1024 MB RAM, 20 GB SSD NVMe, 10 поддоменов, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 3 шт.",
        "99 ₽/мес",
    ),
    (
        "Веб-хостинг",
        "Web Enterprise",
        "Премиум-хостинг с высокой надёжностью.",
        "Безлимит vCPU, 1024 MB RAM, 30 GB SSD NVMe, 10 поддоменов, Управление через Telegram-бота, Защита от DDoS, Бэкапы: 5 шт., Приоритетная поддержка",
        "149 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Mini",
        "Подойдёт для прокси-сервера.",
        "1 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 5 GB SSD NVMe, Всего портов: 2, Управление через Telegram-бота, Бэкапы: 3 шт., Мощная DDoS защита",
        "39 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Start",
        "Подойдёт для маленького сервера с друзьями.",
        "1.5 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 5 GB SSD NVMe, Всего портов: 2, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "49 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Standard",
        "Для средних серверов с модами и игроками.",
        "2 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz, 10 GB SSD NVMe, Всего портов: 4, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "79 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Premium",
        "Для серьёзных проектов и игровых сообществ.",
        "4 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz с приоритетом, 20 GB SSD NVMe, Всего портов: 6, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "169 ₽/мес",
    ),
    (
        "Minecraft-сервера",
        "MC Ultra",
        "Отличный выбор для мини-игр и мультисерверной инфраструктуры.",
        "6 GB RAM DDR4-DDR5, Безлимит vCPU @ 4.4-5.4 GHz с высоким приоритетом, 30 GB SSD NVMe, Всего портов: 6, Управление через Telegram-бота, Бэкапы: 5 шт., Мощная DDoS защита",
        "219 ₽/мес",
    ),
]


def _sync_category_plans(db, category):
    current_names = [p[1] for p in SEED_PLANS if p[0] == category]

    db.query(Plan).filter(
        Plan.category == category, ~Plan.name.in_(current_names)
    ).update({"is_active": False}, synchronize_session=False)

    existing_names = {
        row[0]
        for row in db.query(Plan.name).filter(Plan.category == category).all()
    }

    missing_plans = [p for p in SEED_PLANS if p[0] == category and p[1] not in existing_names]
    for p in missing_plans:
        db.add(Plan(category=p[0], name=p[1], description=p[2], specs=p[3], price=p[4]))

    # Plans that already exist by name still need their price/specs kept in
    # sync with SEED_PLANS - otherwise editing a price here would silently
    # do nothing on an already-initialized database.
    existing_plans = [p for p in SEED_PLANS if p[0] == category and p[1] in existing_names]
    for p in existing_plans:
        db.query(Plan).filter(Plan.category == p[0], Plan.name == p[1]).update(
            {"description": p[2], "specs": p[3], "price": p[4], "is_active": True}
        )


def seed_plans():
    db = get_db()
    seed_categories = {p[0] for p in SEED_PLANS}
    for category in seed_categories:
        _sync_category_plans(db, category)
    db.commit()


@click.command("seed-plans")
def seed_plans_command():
    seed_plans()
    click.echo("Тарифы синхронизированы.")


def run_migrations():
    """Apply any pending Alembic migrations.

    Render's free-tier disk is ephemeral - the SQLite file is wiped on
    every redeploy - so the schema has to be (re)created on every boot
    regardless. Alembic's own version table makes this safe to call on
    every boot (unlike the old raw executescript): it only applies
    revisions that haven't already run, so it's a no-op on a DB that's
    already current (e.g. Postgres in production, un-reset between boots).
    """
    from alembic import command
    from alembic.config import Config

    repo_root = Path(__file__).resolve().parent.parent
    cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(cfg, "head")


def init_app(app):
    global engine, Session

    engine = create_engine(get_database_url(instance_path=app.instance_path))
    Session = scoped_session(sessionmaker(bind=engine))

    app.teardown_appcontext(lambda exc: Session.remove())
    app.cli.add_command(seed_plans_command)

    with app.app_context():
        run_migrations()
        seed_plans()
