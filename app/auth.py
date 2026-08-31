import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
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
