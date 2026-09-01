import hmac
import secrets
from functools import wraps

from flask import abort, redirect, request, session, url_for


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def check_csrf_token():
    token = session.get("csrf_token")
    submitted = request.form.get("csrf_token")
    if not token or not submitted or not hmac.compare_digest(token, submitted):
        abort(400)


def validate_user_session():
    """Clear a session pointing at a user_id that no longer exists in the DB.

    On Render's free tier the SQLite file resets on redeploy, so a browser can
    still hold a valid signed session cookie for a user row that's gone —
    without this, any authenticated action crashes with a FOREIGN KEY error
    instead of asking the visitor to log in again.
    """
    user_id = session.get("user_id")
    if user_id is None:
        return

    from .db import get_db

    exists = get_db().execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    if exists is None:
        session.pop("user_id", None)


def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("shop.admin_login"))
        return view(*args, **kwargs)

    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
