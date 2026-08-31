import hmac
import secrets
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("shop", __name__)


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def check_csrf_token():
    token = session.get("csrf_token")
    submitted = request.form.get("csrf_token")
    if not token or not submitted or not hmac.compare_digest(token, submitted):
        abort(400)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("shop.admin_login"))
        return view(*args, **kwargs)

    return wrapped


@bp.app_context_processor
def inject_csrf_token():
    return {"csrf_token": get_csrf_token()}


@bp.route("/")
def index():
    db = get_db()
    servers = db.execute(
        "SELECT * FROM servers WHERE is_active = 1 ORDER BY id"
    ).fetchall()
    return render_template("index.html", servers=servers)


@bp.route("/order", methods=["POST"])
def order():
    check_csrf_token()

    server_id = request.form.get("server_id", type=int)
    contact_name = request.form.get("contact_name", "").strip()
    contact_info = request.form.get("contact_info", "").strip()
    comment = request.form.get("comment", "").strip()

    if not contact_name or not contact_info:
        flash("Заполните имя и контакт для связи.", "error")
        return redirect(url_for("shop.index"))

    db = get_db()
    server = db.execute(
        "SELECT * FROM servers WHERE id = ? AND is_active = 1", (server_id,)
    ).fetchone()
    if server is None:
        flash("Выбранный тариф недоступен.", "error")
        return redirect(url_for("shop.index"))

    db.execute(
        """
        INSERT INTO orders (server_id, server_name, contact_name, contact_info, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (server["id"], server["name"], contact_name, contact_info, comment),
    )
    db.commit()

    flash("Заявка отправлена! Мы свяжемся с вами в ближайшее время.", "success")
    return redirect(url_for("shop.index"))


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        check_csrf_token()
        password = request.form.get("password", "")
        if check_password_hash(current_app.config["ADMIN_PASSWORD_HASH"], password):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("shop.admin_dashboard"))
        flash("Неверный пароль.", "error")
    return render_template("admin_login.html")


@bp.route("/admin/logout", methods=["POST"])
@login_required
def admin_logout():
    check_csrf_token()
    session.clear()
    return redirect(url_for("shop.admin_login"))


@bp.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return render_template("admin_dashboard.html", orders=orders)
