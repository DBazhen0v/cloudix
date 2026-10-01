from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship


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
    oauth_provider = Column(String)
    oauth_id = Column(String)
    created_at = Column(String, nullable=False, default=_now)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"))
    plan_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="awaiting_payment")
    payment_method = Column(String)
    contact_note = Column(Text)
    connection_info = Column(Text)
    expires_at = Column(String)
    created_at = Column(String, nullable=False, default=_now)

    user = relationship("User")
    plan = relationship("Plan")


class ActionRequest(Base):
    __tablename__ = "action_requests"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(String, nullable=False, default=_now)

    subscription = relationship("Subscription")


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    contact = Column(String)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="new")
    created_at = Column(String, nullable=False, default=_now)

    user = relationship("User")
