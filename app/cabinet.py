from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .constants import (
    ACTIONS,
    ORDER_STATUSES,
    SERVER_STATUSES,
    SUBSCRIPTION_STATUSES,
    TICKET_PRIORITIES,
    TICKET_STATUSES,
)
from .db import get_db
from .models import (
    ActionRequest,
    Notification,
    Order,
    Plan,
    Server,
    Subscription,
    SupportTicket,
    TicketMessage,
    User,
    _now,
)
from .security import check_csrf_token

bp = Blueprint("cabinet", __name__, url_prefix="/cabinet")


@bp.before_request
def load_current_user():
    if not session.get("user_id"):
        return redirect(url_for("auth.login", next=request.path))
    g.user = get_db().query(User).filter_by(id=session["user_id"]).first()
    if g.user is None:
        session.clear()
        return redirect(url_for("auth.login", next=request.path))


@bp.app_context_processor
def inject_unread_notifications():
    if not session.get("user_id"):
        return {}
    db = get_db()
    count = (
        db.query(Notification)
        .filter_by(user_id=session["user_id"], is_read=False)
        .count()
    )
    return {"unread_notifications": count}


@bp.route("")
def index():
    db = get_db()
    servers_count = db.query(Server).filter_by(user_id=g.user.id).count()
    active_servers_count = db.query(Server).filter_by(user_id=g.user.id, status="active").count()
    pending_orders_count = db.query(Order).filter_by(user_id=g.user.id, status="pending").count()
    unread_notifications_count = (
        db.query(Notification).filter_by(user_id=g.user.id, is_read=False).count()
    )
    recent_orders = (
        db.query(Order).filter_by(user_id=g.user.id).order_by(Order.created_at.desc()).limit(3).all()
    )
    recent_notifications = (
        db.query(Notification)
        .filter_by(user_id=g.user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "cabinet/overview.html",
        servers_count=servers_count,
        active_servers_count=active_servers_count,
        pending_orders_count=pending_orders_count,
        unread_notifications_count=unread_notifications_count,
        recent_orders=recent_orders,
        recent_notifications=recent_notifications,
        order_statuses=ORDER_STATUSES,
        active_nav="overview",
    )


@bp.route("/servers")
def servers():
    db = get_db()
    rows = (
        db.query(Server)
        .filter_by(user_id=g.user.id)
        .order_by(Server.created_at.desc())
        .all()
    )
    plans = db.query(Plan).filter_by(is_active=True).order_by(Plan.id).all()
    return render_template(
        "cabinet/servers.html",
        servers=rows,
        plans=plans,
        server_statuses=SERVER_STATUSES,
        subscription_statuses=SUBSCRIPTION_STATUSES,
        actions=ACTIONS,
        active_nav="servers",
    )


@bp.route("/action", methods=["POST"])
def request_action():
    check_csrf_token()

    server_id = request.form.get("server_id", type=int)
    action = request.form.get("action", "")
    details = request.form.get("details", "").strip()

    if action not in ACTIONS:
        abort(400)

    db = get_db()
    server = db.query(Server).filter_by(id=server_id).first()

    if server is None:
        abort(404)
    if server.user_id != g.user.id:
        abort(403)

    db.add(ActionRequest(server_id=server_id, action=action, details=details or None))
    db.commit()

    flash("Заявка отправлена администратору.", "success")
    return redirect(url_for("cabinet.servers"))


@bp.route("/orders")
def orders():
    db = get_db()
    rows = (
        db.query(Order).filter_by(user_id=g.user.id).order_by(Order.created_at.desc()).all()
    )
    return render_template("cabinet/orders.html", orders=rows, order_statuses=ORDER_STATUSES, active_nav="orders")


@bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    db = get_db()
    order = db.query(Order).filter_by(id=order_id).first()
    if order is None:
        abort(404)
    if order.user_id != g.user.id:
        abort(403)
    return render_template(
        "cabinet/order_detail.html", order=order, order_statuses=ORDER_STATUSES, active_nav="orders"
    )


@bp.route("/subscriptions")
def subscriptions():
    db = get_db()
    rows = (
        db.query(Subscription)
        .join(Server, Server.id == Subscription.server_id)
        .filter(Server.user_id == g.user.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return render_template(
        "cabinet/subscriptions.html",
        subscriptions=rows,
        subscription_statuses=SUBSCRIPTION_STATUSES,
        active_nav="subscriptions",
    )


@bp.route("/invoices")
def invoices():
    db = get_db()
    rows = (
        db.query(Order)
        .filter(Order.user_id == g.user.id, Order.paid_at.isnot(None))
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("cabinet/invoices.html", orders=rows, active_nav="invoices")


@bp.route("/invoices/<int:order_id>")
def invoice_detail(order_id):
    db = get_db()
    order = db.query(Order).filter_by(id=order_id).first()
    if order is None:
        abort(404)
    if order.user_id != g.user.id:
        abort(403)
    if order.paid_at is None:
        abort(404)
    return render_template("invoice.html", order=order)


@bp.route("/support")
def support_list():
    db = get_db()
    rows = (
        db.query(SupportTicket)
        .filter_by(user_id=g.user.id)
        .order_by(SupportTicket.updated_at.desc())
        .all()
    )
    return render_template(
        "cabinet/support_list.html",
        tickets=rows,
        ticket_statuses=TICKET_STATUSES,
        ticket_priorities=TICKET_PRIORITIES,
        active_nav="support",
    )


@bp.route("/support/<int:ticket_id>")
def support_thread(ticket_id):
    db = get_db()
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if ticket is None:
        abort(404)
    if ticket.user_id != g.user.id:
        abort(403)
    messages = (
        db.query(TicketMessage)
        .filter_by(ticket_id=ticket_id)
        .order_by(TicketMessage.created_at)
        .all()
    )
    return render_template(
        "cabinet/support_thread.html",
        ticket=ticket,
        messages=messages,
        ticket_statuses=TICKET_STATUSES,
        ticket_priorities=TICKET_PRIORITIES,
        active_nav="support",
    )


@bp.route("/support/<int:ticket_id>/reply", methods=["POST"])
def support_reply(ticket_id):
    check_csrf_token()

    body = request.form.get("message", "").strip()
    if not body:
        flash("Напишите сообщение перед отправкой.", "error")
        return redirect(url_for("cabinet.support_thread", ticket_id=ticket_id))

    db = get_db()
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if ticket is None:
        abort(404)
    if ticket.user_id != g.user.id:
        abort(403)

    db.add(TicketMessage(ticket_id=ticket_id, author_type="user", author_user_id=g.user.id, body=body))
    ticket.status = "open"
    ticket.updated_at = _now()
    db.commit()

    flash("Сообщение отправлено.", "success")
    return redirect(url_for("cabinet.support_thread", ticket_id=ticket_id))


@bp.route("/notifications")
def notifications():
    db = get_db()
    rows = (
        db.query(Notification)
        .filter_by(user_id=g.user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    db.query(Notification).filter_by(user_id=g.user.id, is_read=False).update({"is_read": True})
    db.commit()
    return render_template("cabinet/notifications.html", notifications=rows, active_nav="notifications")


@bp.route("/profile")
def profile():
    auth_method = "Google" if g.user.oauth_provider == "google" else "Email и пароль"
    return render_template("cabinet/profile.html", auth_method=auth_method, active_nav="profile")


@bp.route("/profile", methods=["POST"])
def update_profile():
    check_csrf_token()

    name = request.form.get("name", "").strip()
    db = get_db()
    g.user.name = name or None
    db.commit()

    flash("Профиль обновлён.", "success")
    return redirect(url_for("cabinet.profile"))


@bp.route("/password", methods=["POST"])
def change_password():
    check_csrf_token()

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not check_password_hash(g.user.password_hash, current_password):
        flash("Текущий пароль неверен.", "error")
    elif len(new_password) < 8:
        flash("Новый пароль должен быть не короче 8 символов.", "error")
    elif new_password != confirm_password:
        flash("Пароли не совпадают.", "error")
    else:
        db = get_db()
        g.user.password_hash = generate_password_hash(new_password)
        db.commit()
        flash("Пароль изменён.", "success")

    return redirect(url_for("cabinet.profile"))
