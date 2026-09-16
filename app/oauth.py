import os

from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_app(app):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    app.config["GOOGLE_OAUTH_CONFIGURED"] = bool(client_id and client_secret)

    oauth.init_app(app)

    if app.config["GOOGLE_OAUTH_CONFIGURED"]:
        oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
