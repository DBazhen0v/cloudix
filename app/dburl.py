import os
from pathlib import Path


def get_database_url(instance_path=None):
    """Single source of truth for the DB connection string, shared by the
    Flask app (app/db.py) and Alembic (migrations/env.py).

    DATABASE_URL is required in production (Render injects it once a
    Postgres instance is linked). Locally, with no DATABASE_URL set, this
    falls back to the SQLite file under instance/ that the app has always
    used - lets Alembic/the app run without any extra setup before the
    Postgres cutover.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # Render's Postgres connection string uses the legacy "postgres://"
        # scheme; SQLAlchemy 2.x only accepts "postgresql://".
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    if instance_path is None:
        raise RuntimeError("DATABASE_URL is not set and no instance_path fallback was given")
    return f"sqlite:///{Path(instance_path) / 'shop.sqlite3'}"
