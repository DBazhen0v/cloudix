from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, backref, relationship


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class Base(DeclarativeBase):
    pass


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    specs = Column(Text, nullable=False)
    price = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("oauth_provider", "oauth_id", name="idx_users_oauth"),)

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    status = Column(String, nullable=False, default="active")
    oauth_provider = Column(String)
    oauth_id = Column(String)
    created_at = Column(String, nullable=False, default=_now)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"))
    plan_name = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="RUB")
    payment_method = Column(String)
    contact_note = Column(Text)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(String, nullable=False, default=_now)
    paid_at = Column(String)

    user = relationship("User")
    plan = relationship("Plan")


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"))
    name = Column(String, nullable=False)
    hostname = Column(String)
    ipv4 = Column(String)
    ipv6 = Column(String)
    location = Column(String)
    operating_system = Column(String)
    status = Column(String, nullable=False, default="provisioning")
    connection_info = Column(Text)
    created_at = Column(String, nullable=False, default=_now)

    order = relationship("Order", backref=backref("server", uselist=False))
    user = relationship("User")
    plan = relationship("Plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"))
    billing_period = Column(String, nullable=False, default="monthly")
    next_billing_date = Column(String)
    status = Column(String, nullable=False, default="active")
    created_at = Column(String, nullable=False, default=_now)

    server = relationship("Server", backref=backref("subscription", uselist=False))
    plan = relationship("Plan")


class ActionRequest(Base):
    __tablename__ = "action_requests"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(String, nullable=False, default=_now)

    server = relationship("Server")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    contact = Column(String)
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    priority = Column(String, nullable=False, default="normal")
    created_at = Column(String, nullable=False, default=_now)
    updated_at = Column(String, nullable=False, default=_now)

    user = relationship("User")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    author_type = Column(String, nullable=False)
    author_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    body = Column(Text, nullable=False)
    created_at = Column(String, nullable=False, default=_now)

    ticket = relationship("SupportTicket", backref="messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text)
    link = Column(String)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(String, nullable=False, default=_now)

    user = relationship("User")
