from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from .constants import ACTIONS, PAYMENT_METHODS
from .db import get_db
from .security import check_csrf_token, login_required

bp = Blueprint("cabinet", __name__, url_prefix="/cabinet")


@bp.route("")
@login_required
def index():
    db = get_db()
    subscriptions = db.execute(
        """
        SELECT s.*,
               (SELECT COUNT(*) FROM action_requests a
                WHERE a.subscription_id = s.id AND a.status = 'pending') AS pending_actions
        FROM subscriptions s
        WHERE s.user_id = ?
        ORDER BY s.created_at DESC
        """,
        (session["user_id"],),
    ).fetchall()
    plans = db.execute("SELECT * FROM plans WHERE is_active = 1 ORDER BY id").fetchall()
    user = db.execute(
        "SELECT email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    return render_template(
        "cabinet.html",
        subscriptions=subscriptions,
        plans=plans,
        payment_methods=PAYMENT_METHODS,
        user_email=user["email"],
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
    subscription = db.execute(
        "SELECT * FROM subscriptions WHERE id = ?", (subscription_id,)
    ).fetchone()

    if subscription is None:
        abort(404)
    if subscription["user_id"] != session["user_id"]:
        abort(403)

    db.execute(
        "INSERT INTO action_requests (subscription_id, action, details) VALUES (?, ?, ?)",
        (subscription_id, action, details or None),
    )
    db.commit()

    flash("Заявка отправлена администратору.", "success")
    return redirect(url_for("cabinet.index"))
