from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from .constants import PAYMENT_METHODS
from .db import get_db
from .security import admin_login_required, check_csrf_token, get_csrf_token

bp = Blueprint("shop", __name__)


@bp.app_context_processor
def inject_globals():
    return {
        "csrf_token": get_csrf_token(),
        "user_logged_in": bool(session.get("user_id")),
        "support_telegram_url": current_app.config["SUPPORT_TELEGRAM_URL"],
        "support_email": current_app.config["SUPPORT_EMAIL"],
    }


@bp.route("/")
def index():
    db = get_db()
    plans = db.execute("SELECT * FROM plans WHERE is_active = 1 ORDER BY id").fetchall()

    plan_groups = {}
    for plan in plans:
        plan_groups.setdefault(plan["category"], []).append(plan)

    return render_template(
        "index.html",
        plan_groups=plan_groups,
        crypto_wallet_address=current_app.config["CRYPTO_WALLET_ADDRESS"],
    )


@bp.route("/order", methods=["POST"])
def order():
    check_csrf_token()

    if not session.get("user_id"):
        flash("Войдите или зарегистрируйтесь, чтобы оставить заявку.", "error")
        return redirect(url_for("auth.login", next=url_for("shop.index") + "#plans"))

    plan_id = request.form.get("plan_id", type=int)
    contact = request.form.get("contact", "").strip()
    comment = request.form.get("comment", "").strip()
    payment_method = request.form.get("payment_method", "")

    contact_note = "\n".join(
        part for part in (f"Контакт: {contact}" if contact else "", comment) if part
    )

    if payment_method not in PAYMENT_METHODS:
        payment_method = None

    db = get_db()
    plan = db.execute(
        "SELECT * FROM plans WHERE id = ? AND is_active = 1", (plan_id,)
    ).fetchone()
    if plan is None:
        flash("Выбранный тариф недоступен.", "error")
        return redirect(url_for("shop.index"))

    db.execute(
        """
        INSERT INTO subscriptions (user_id, plan_id, plan_name, contact_note, payment_method)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session["user_id"], plan["id"], plan["name"], contact_note or None, payment_method),
    )
    db.commit()

    flash(
        "Заявка отправлена. Мы получили вашу заявку — администратор свяжется с вами "
        "для подтверждения оплаты и настройки.",
        "success",
    )
    return redirect(url_for("cabinet.index"))


@bp.route("/support", methods=["POST"])
def support_message():
    check_csrf_token()

    message = request.form.get("message", "").strip()
    contact = request.form.get("contact", "").strip()
    next_url = request.form.get("next", "")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("shop.index")

    if not message:
        flash("Напишите сообщение перед отправкой.", "error")
        return redirect(next_url)

    db = get_db()
    db.execute(
        "INSERT INTO support_messages (user_id, contact, message) VALUES (?, ?, ?)",
        (session.get("user_id"), contact or None, message),
    )
    db.commit()

    flash("Сообщение отправлено — мы свяжемся с вами.", "success")
    return redirect(next_url)


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
@admin_login_required
def admin_logout():
    check_csrf_token()
    session.clear()
    return redirect(url_for("shop.admin_login"))


@bp.route("/admin")
@admin_login_required
def admin_dashboard():
    db = get_db()
    subscriptions = db.execute(
        """
        SELECT s.*, u.email AS user_email
        FROM subscriptions s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.created_at DESC
        """
    ).fetchall()
    action_requests = db.execute(
        """
        SELECT a.*, s.plan_name, u.email AS user_email
        FROM action_requests a
        JOIN subscriptions s ON s.id = a.subscription_id
        JOIN users u ON u.id = s.user_id
        WHERE a.status = 'pending'
        ORDER BY a.created_at
        """
    ).fetchall()
    support_messages = db.execute(
        """
        SELECT sm.*, u.email AS user_email
        FROM support_messages sm
        LEFT JOIN users u ON u.id = sm.user_id
        WHERE sm.status = 'new'
        ORDER BY sm.created_at
        """
    ).fetchall()
    return render_template(
        "admin_dashboard.html",
        subscriptions=subscriptions,
        action_requests=action_requests,
        support_messages=support_messages,
        payment_methods=PAYMENT_METHODS,
    )


@bp.route("/admin/subscriptions/<int:subscription_id>", methods=["POST"])
@admin_login_required
def admin_update_subscription(subscription_id):
    check_csrf_token()

    status = request.form.get("status", "")
    connection_info = request.form.get("connection_info", "").strip()
    expires_at = request.form.get("expires_at", "").strip()

    if status not in {"awaiting_payment", "active", "suspended"}:
        flash("Некорректный статус.", "error")
        return redirect(url_for("shop.admin_dashboard"))

    db = get_db()
    db.execute(
        """
        UPDATE subscriptions
        SET status = ?, connection_info = ?, expires_at = ?
        WHERE id = ?
        """,
        (status, connection_info or None, expires_at or None, subscription_id),
    )
    db.commit()

    flash("Подписка обновлена.", "success")
    return redirect(url_for("shop.admin_dashboard"))


@bp.route("/admin/action-requests/<int:action_id>/done", methods=["POST"])
@admin_login_required
def admin_complete_action(action_id):
    check_csrf_token()

    db = get_db()
    db.execute("UPDATE action_requests SET status = 'done' WHERE id = ?", (action_id,))
    db.commit()

    flash("Заявка отмечена выполненной.", "success")
    return redirect(url_for("shop.admin_dashboard"))


@bp.route("/admin/support-messages/<int:message_id>/done", methods=["POST"])
@admin_login_required
def admin_complete_support_message(message_id):
    check_csrf_token()

    db = get_db()
    db.execute("UPDATE support_messages SET status = 'done' WHERE id = ?", (message_id,))
    db.commit()

    flash("Сообщение отмечено обработанным.", "success")
    return redirect(url_for("shop.admin_dashboard"))
