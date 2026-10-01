from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash

from .constants import (
    ACTIONS,
    ORDER_STATUSES,
    PAYMENT_METHODS,
    SERVER_STATUSES,
    TICKET_PRIORITIES,
    TICKET_STATUSES,
)
from .db import get_db
from .models import ActionRequest, Order, Server, Subscription, SupportTicket, TicketMessage, _now
from .notifications import create_notification
from .security import admin_login_required, check_csrf_token

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _add_days(days):
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")


@bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        check_csrf_token()
        password = request.form.get("password", "")
        if check_password_hash(current_app.config["ADMIN_PASSWORD_HASH"], password):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))
        flash("Неверный пароль.", "error")
    return render_template("admin_login.html")


@bp.route("/logout", methods=["POST"])
@admin_login_required
def admin_logout():
    check_csrf_token()
    session.clear()
    return redirect(url_for("admin.admin_login"))


@bp.route("")
@admin_login_required
def dashboard():
    db = get_db()
    orders = (
        db.query(Order)
        .options(joinedload(Order.user))
        .order_by(Order.created_at.desc())
        .all()
    )
    servers = (
        db.query(Server)
        .options(joinedload(Server.user))
        .order_by(Server.created_at.desc())
        .all()
    )
    action_requests = (
        db.query(ActionRequest)
        .options(joinedload(ActionRequest.server).joinedload(Server.user))
        .filter(ActionRequest.status == "pending")
        .order_by(ActionRequest.created_at)
        .all()
    )
    tickets = (
        db.query(SupportTicket)
        .options(joinedload(SupportTicket.user))
        .filter(SupportTicket.status != "closed")
        .order_by(SupportTicket.updated_at.desc())
        .all()
    )
    return render_template(
        "admin_dashboard.html",
        orders=orders,
        servers=servers,
        action_requests=action_requests,
        tickets=tickets,
        payment_methods=PAYMENT_METHODS,
        order_statuses=ORDER_STATUSES,
        server_statuses=SERVER_STATUSES,
        ticket_statuses=TICKET_STATUSES,
        actions=ACTIONS,
    )


@bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_login_required
def update_order_status(order_id):
    check_csrf_token()

    status = request.form.get("status", "")
    if status not in ORDER_STATUSES:
        abort(400)

    db = get_db()
    order = db.query(Order).filter_by(id=order_id).first()
    if order is None:
        abort(404)

    was_paid = order.paid_at is not None
    order.status = status

    if status == "paid" and not was_paid:
        order.paid_at = _now()
        server = Server(
            order_id=order.id,
            user_id=order.user_id,
            plan_id=order.plan_id,
            name=order.plan_name,
            status="provisioning",
        )
        db.add(server)
        db.flush()
        db.add(
            Subscription(
                server_id=server.id,
                plan_id=order.plan_id,
                next_billing_date=_add_days(30),
            )
        )
        create_notification(
            db,
            order.user_id,
            "order_paid",
            "Оплата подтверждена",
            f"Заказ №{order.id} оплачен, сервер настраивается.",
            link=url_for("cabinet.order_detail", order_id=order.id),
        )

    db.commit()

    flash("Заказ обновлён.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/servers/<int:server_id>", methods=["POST"])
@admin_login_required
def update_server(server_id):
    check_csrf_token()

    status = request.form.get("status", "")
    if status not in SERVER_STATUSES:
        abort(400)

    db = get_db()
    server = db.query(Server).filter_by(id=server_id).first()
    if server is None:
        abort(404)

    old_status = server.status
    server.hostname = request.form.get("hostname", "").strip() or None
    server.ipv4 = request.form.get("ipv4", "").strip() or None
    server.ipv6 = request.form.get("ipv6", "").strip() or None
    server.location = request.form.get("location", "").strip() or None
    server.operating_system = request.form.get("operating_system", "").strip() or None
    server.connection_info = request.form.get("connection_info", "").strip() or None
    server.status = status

    if status != old_status:
        create_notification(
            db,
            server.user_id,
            "server_status_changed",
            f"Статус сервера изменён: {SERVER_STATUSES.get(status, status)}",
            link=url_for("cabinet.servers"),
        )

    db.commit()

    flash("Сервер обновлён.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/action-requests/<int:action_id>/done", methods=["POST"])
@admin_login_required
def complete_action(action_id):
    check_csrf_token()

    db = get_db()
    action = db.query(ActionRequest).options(joinedload(ActionRequest.server)).filter_by(id=action_id).first()
    if action is None:
        abort(404)

    action.status = "done"
    create_notification(
        db,
        action.server.user_id,
        "action_request_done",
        f"Заявка «{ACTIONS.get(action.action, action.action)}» выполнена",
        link=url_for("cabinet.servers"),
    )
    db.commit()

    flash("Заявка отмечена выполненной.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/tickets/<int:ticket_id>")
@admin_login_required
def ticket_thread(ticket_id):
    db = get_db()
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if ticket is None:
        abort(404)
    messages = (
        db.query(TicketMessage).filter_by(ticket_id=ticket_id).order_by(TicketMessage.created_at).all()
    )
    return render_template(
        "admin_ticket_thread.html",
        ticket=ticket,
        messages=messages,
        ticket_statuses=TICKET_STATUSES,
        ticket_priorities=TICKET_PRIORITIES,
    )


@bp.route("/tickets/<int:ticket_id>/reply", methods=["POST"])
@admin_login_required
def ticket_reply(ticket_id):
    check_csrf_token()

    body = request.form.get("message", "").strip()
    status = request.form.get("status", "")
    priority = request.form.get("priority", "")

    db = get_db()
    ticket = db.query(SupportTicket).filter_by(id=ticket_id).first()
    if ticket is None:
        abort(404)

    if body:
        db.add(TicketMessage(ticket_id=ticket_id, author_type="admin", body=body))
    if status in TICKET_STATUSES:
        ticket.status = status
    if priority in TICKET_PRIORITIES:
        ticket.priority = priority
    ticket.updated_at = _now()

    if body and ticket.user_id:
        create_notification(
            db,
            ticket.user_id,
            "ticket_reply",
            f"Ответ в обращении «{ticket.subject}»",
            link=url_for("cabinet.support_thread", ticket_id=ticket.id),
        )

    db.commit()

    flash("Обращение обновлено.", "success")
    return redirect(url_for("admin.ticket_thread", ticket_id=ticket_id))
