import re
import secrets

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .oauth import oauth
from .security import check_csrf_token

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _safe_next(next_url):
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for("cabinet.index")


@bp.route("/register", methods=["GET", "POST"])
def register():
    next_url = request.values.get("next", "")

    if request.method == "POST":
        check_csrf_token()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        next_url = request.form.get("next", "")

        if not EMAIL_RE.match(email):
            flash("Введите корректный email.", "error")
        elif len(password) < 8:
            flash("Пароль должен быть не короче 8 символов.", "error")
        elif password != confirm:
            flash("Пароли не совпадают.", "error")
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing is not None:
                flash("Этот email уже зарегистрирован.", "error")
            else:
                cursor = db.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )
                db.commit()
                session.clear()
                session["user_id"] = cursor.lastrowid
                return redirect(_safe_next(next_url))

    return render_template("register.html", next_url=next_url)


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.values.get("next", "")

    if request.method == "POST":
        check_csrf_token()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Неверный email или пароль.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(_safe_next(next_url))

    return render_template("login.html", next_url=next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf_token()
    session.clear()
    return redirect(url_for("shop.index"))


@bp.route("/google/login")
def google_login():
    if not current_app.config.get("GOOGLE_OAUTH_CONFIGURED"):
        flash("Вход через Google пока не настроен.", "error")
        return redirect(url_for("auth.login"))

    session["oauth_next"] = _safe_next(request.args.get("next", ""))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/google/callback")
def google_callback():
    if not current_app.config.get("GOOGLE_OAUTH_CONFIGURED"):
        flash("Вход через Google пока не настроен.", "error")
        return redirect(url_for("auth.login"))

    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") or {}

    if not userinfo.get("email") or not userinfo.get("email_verified"):
        flash("Google не подтвердил email — попробуйте другой способ входа.", "error")
        return redirect(url_for("auth.login"))

    email = userinfo["email"].strip().lower()
    google_sub = userinfo["sub"]

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE oauth_provider = 'google' AND oauth_id = ?",
        (google_sub,),
    ).fetchone()

    if user is None:
        # A password account with this Google-verified email already
        # exists - link the Google identity to it instead of rejecting or
        # creating a duplicate (email is UNIQUE), so either sign-in method
        # works from now on.
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is not None:
            db.execute(
                "UPDATE users SET oauth_provider = 'google', oauth_id = ? WHERE id = ?",
                (google_sub, user["id"]),
            )
            db.commit()
        else:
            # No password is ever set for a Google-only account - store an
            # unusable random hash so the column can stay NOT NULL and the
            # password-login path can never authenticate this row.
            placeholder_hash = generate_password_hash(secrets.token_urlsafe(32))
            cursor = db.execute(
                "INSERT INTO users (email, password_hash, oauth_provider, oauth_id) VALUES (?, ?, 'google', ?)",
                (email, placeholder_hash, google_sub),
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()

    session.clear()
    session["user_id"] = user["id"]
    next_url = session.pop("oauth_next", None) or url_for("cabinet.index")
    return redirect(next_url)
