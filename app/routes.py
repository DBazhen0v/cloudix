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
from .models import Order, Plan, SupportTicket, TicketMessage
from .notifications import create_notification
from .security import check_csrf_token, get_csrf_token

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

    new_order = Order(
        user_id=session["user_id"],
        plan_id=plan.id,
        plan_name=plan.name,
        amount=_plan_price_value(plan),
        contact_note=contact_note or None,
        payment_method=payment_method,
    )
    db.add(new_order)
    db.flush()
    create_notification(
        db,
        session["user_id"],
        "order_placed",
        f"Заказ №{new_order.id} создан",
        "Ожидает подтверждения оплаты администратором.",
        link=url_for("cabinet.order_detail", order_id=new_order.id),
    )
    db.commit()

    flash(
        "Заявка отправлена. Мы получили вашу заявку — администратор свяжется с вами "
        "для подтверждения оплаты и настройки.",
        "success",
    )
    return redirect(url_for("cabinet.orders"))


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
    user_id = session.get("user_id")

    ticket = None
    if user_id:
        ticket = (
            db.query(SupportTicket)
            .filter(SupportTicket.user_id == user_id, SupportTicket.status != "closed")
            .order_by(SupportTicket.updated_at.desc())
            .first()
        )

    if ticket is None:
        ticket = SupportTicket(
            user_id=user_id,
            contact=contact or None,
            subject=message[:60],
        )
        db.add(ticket)
        db.flush()

    db.add(TicketMessage(ticket_id=ticket.id, author_type="user", author_user_id=user_id, body=message))
    db.commit()

    flash("Сообщение отправлено — мы свяжемся с вами.", "success")
    return redirect(next_url)
