import os
from pathlib import Path

from flask import Flask


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["ADMIN_PASSWORD_HASH"] = os.environ["ADMIN_PASSWORD_HASH"]
    app.config["DATABASE"] = str(Path(app.instance_path) / "shop.sqlite3")
    app.config["CRYPTO_WALLET_ADDRESS"] = os.environ.get("CRYPTO_WALLET_ADDRESS", "")
    app.config["SUPPORT_TELEGRAM_URL"] = os.environ.get("SUPPORT_TELEGRAM_URL", "")
    app.config["SUPPORT_EMAIL"] = os.environ.get("SUPPORT_EMAIL", "")

    os.makedirs(app.instance_path, exist_ok=True)

    from . import db
    db.init_app(app)

    from . import security
    app.before_request(security.validate_user_session)

    from . import routes
    app.register_blueprint(routes.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import cabinet
    app.register_blueprint(cabinet.bp)

    return app
