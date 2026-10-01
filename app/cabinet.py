from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, select

from .constants import ACTIONS, PAYMENT_METHODS
from .db import get_db
from .models import ActionRequest, Plan, Subscription, User
from .security import check_csrf_token, login_required

bp = Blueprint("cabinet", __name__, url_prefix="/cabinet")


@bp.route("")
@login_required
def index():
    db = get_db()
    pending_actions = (
        select(func.count(ActionRequest.id))
        .where(ActionRequest.subscription_id == Subscription.id, ActionRequest.status == "pending")
        .correlate(Subscription)
        .scalar_subquery()
    )
    subscriptions = db.execute(
        select(
            Subscription.id,
            Subscription.plan_id,
            Subscription.plan_name,
            Subscription.status,
            Subscription.payment_method,
            Subscription.connection_info,
            Subscription.expires_at,
            Subscription.created_at,
            pending_actions.label("pending_actions"),
        )
        .where(Subscription.user_id == session["user_id"])
        .order_by(Subscription.created_at.desc())
    ).mappings().all()
    plans = db.query(Plan).filter_by(is_active=True).order_by(Plan.id).all()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    return render_template(
        "cabinet.html",
        subscriptions=subscriptions,
        plans=plans,
        payment_methods=PAYMENT_METHODS,
        user_email=user.email,
    )


@bp.route("/action", methods=["POST"])
@login_required
def request_action():
    check_csrf_token()

    subscription_id = request.form.get("subscription_id", type=int)
    action = request.form.get("action", "")
    details = request.form.get("details", "").strip()

    if action not in ACTIONS:
        abort(400)

    db = get_db()
    subscription = db.query(Subscription).filter_by(id=subscription_id).first()

    if subscription is None:
        abort(404)
    if subscription.user_id != session["user_id"]:
        abort(403)

    db.add(ActionRequest(subscription_id=subscription_id, action=action, details=details or None))
    db.commit()

    flash("Заявка отправлена администратору.", "success")
    return redirect(url_for("cabinet.index"))
