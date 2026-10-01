import re

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
from sqlalchemy import select
from werkzeug.security import check_password_hash

from .constants import (
    HERO_MAP_BOUNDS,
    HERO_MAP_VIEW_HEIGHT,
    HERO_MAP_VIEW_WIDTH,
    PAYMENT_METHODS,
    PLAN_CATEGORY_ORDER,
    SERVER_LINKS,
    SERVER_LOCATIONS,
)
from .db import get_db
from .models import ActionRequest, Plan, SupportMessage, Subscription, User
from .security import admin_login_required, check_csrf_token, get_csrf_token

bp = Blueprint("shop", __name__)


def _plan_price_value(plan):
    match = re.match(r"\d+", plan.price)
    return int(match.group()) if match else 0


def _category_sort_key(category):
    if category in PLAN_CATEGORY_ORDER:
        return (0, PLAN_CATEGORY_ORDER.index(category))
    return (1, category)


@bp.app_context_processor
def inject_globals():
    return {
        "csrf_token": get_csrf_token(),
        "user_logged_in": bool(session.get("user_id")),
        "support_telegram_url": current_app.config["SUPPORT_TELEGRAM_URL"],
        "support_email": current_app.config["SUPPORT_EMAIL"],
        "google_oauth_enabled": current_app.config.get("GOOGLE_OAUTH_CONFIGURED", False),
    }


@bp.route("/")
def index():
    db = get_db()
    plans = db.query(Plan).filter_by(is_active=True).order_by(Plan.id).all()

    unordered_groups = {}
    for plan in plans:
        unordered_groups.setdefault(plan.category, []).append(plan)

    plan_groups = {}
    for category in sorted(unordered_groups, key=_category_sort_key):
        plan_groups[category] = sorted(unordered_groups[category], key=_plan_price_value)

    return render_template(
        "index.html",
        plan_groups=plan_groups,
        crypto_wallet_address=current_app.config["CRYPTO_WALLET_ADDRESS"],
        server_locations=SERVER_LOCATIONS,
        server_links=SERVER_LINKS,
        hero_map_bounds=HERO_MAP_BOUNDS,
        hero_map_view_width=HERO_MAP_VIEW_WIDTH,
        hero_map_view_height=HERO_MAP_VIEW_HEIGHT,
    )


@bp.route("/terms")
def terms():
    return render_template("terms.html")


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
    plan = db.query(Plan).filter_by(id=plan_id, is_active=True).first()
    if plan is None:
        flash("Выбранный тариф недоступен.", "error")
        return redirect(url_for("shop.index"))

    db.add(
        Subscription(
            user_id=session["user_id"],
            plan_id=plan.id,
            plan_name=plan.name,
            contact_note=contact_note or None,
            payment_method=payment_method,
        )
    )
    db.commit()

    flash(
        "Заявка отправлена. Мы получили вашу заявку — администратор свяжется с вами "
        "для подтверждения оплаты и настройки.",
        "success",
    )
    return redirect(url_for("cabinet.index"))


@bp.route("/support")
def support_page():
    return render_template("support.html")


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
    db.add(SupportMessage(user_id=session.get("user_id"), contact=contact or None, message=message))
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
        select(
            Subscription.id,
            Subscription.plan_id,
            Subscription.plan_name,
            Subscription.status,
            Subscription.payment_method,
            Subscription.contact_note,
            Subscription.connection_info,
            Subscription.expires_at,
            Subscription.created_at,
            User.email.label("user_email"),
        )
        .join(User, User.id == Subscription.user_id)
        .order_by(Subscription.created_at.desc())
    ).mappings().all()
    action_requests = db.execute(
        select(
            ActionRequest.id,
            ActionRequest.action,
            ActionRequest.details,
            ActionRequest.created_at,
            Subscription.plan_name,
            User.email.label("user_email"),
        )
        .join(Subscription, Subscription.id == ActionRequest.subscription_id)
        .join(User, User.id == Subscription.user_id)
        .where(ActionRequest.status == "pending")
        .order_by(ActionRequest.created_at)
    ).mappings().all()
    support_messages = db.execute(
        select(
            SupportMessage.id,
            SupportMessage.contact,
            SupportMessage.message,
            SupportMessage.created_at,
            User.email.label("user_email"),
        )
        .outerjoin(User, User.id == SupportMessage.user_id)
        .where(SupportMessage.status == "new")
        .order_by(SupportMessage.created_at)
    ).mappings().all()
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
    db.query(Subscription).filter_by(id=subscription_id).update(
        {
            "status": status,
            "connection_info": connection_info or None,
            "expires_at": expires_at or None,
        }
    )
    db.commit()

    flash("Подписка обновлена.", "success")
    return redirect(url_for("shop.admin_dashboard"))


@bp.route("/admin/action-requests/<int:action_id>/done", methods=["POST"])
@admin_login_required
def admin_complete_action(action_id):
    check_csrf_token()

    db = get_db()
    db.query(ActionRequest).filter_by(id=action_id).update({"status": "done"})
    db.commit()

    flash("Заявка отмечена выполненной.", "success")
    return redirect(url_for("shop.admin_dashboard"))


@bp.route("/admin/support-messages/<int:message_id>/done", methods=["POST"])
@admin_login_required
def admin_complete_support_message(message_id):
    check_csrf_token()

    db = get_db()
    db.query(SupportMessage).filter_by(id=message_id).update({"status": "done"})
    db.commit()

    flash("Сообщение отмечено обработанным.", "success")
    return redirect(url_for("shop.admin_dashboard"))
