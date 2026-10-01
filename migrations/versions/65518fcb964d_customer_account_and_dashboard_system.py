"""customer account and dashboard system

Revision ID: 65518fcb964d
Revises: b5c615927c0d
Create Date: 2026-10-01 15:52:21.203065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65518fcb964d'
down_revision: Union[str, Sequence[str], None] = 'b5c615927c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    `subscriptions` and `action_requests` are dropped and recreated rather
    than altered column-by-column: their shape changes too much for a
    clean ALTER sequence (SQLite can't drop/rename unnamed constraints),
    and there is no production data to preserve (the app is pre-launch;
    this mirrors the "clean start" decision already made for the Postgres
    cutover).
    """
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('plan_name', sa.String(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(), nullable=False),
    sa.Column('payment_method', sa.String(), nullable=True),
    sa.Column('contact_note', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.Column('paid_at', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('servers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('hostname', sa.String(), nullable=True),
    sa.Column('ipv4', sa.String(), nullable=True),
    sa.Column('ipv6', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('operating_system', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('connection_info', sa.Text(), nullable=True),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('link', sa.String(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('support_tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('contact', sa.String(), nullable=True),
    sa.Column('subject', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('priority', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.Column('updated_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ticket_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('author_type', sa.String(), nullable=False),
    sa.Column('author_user_id', sa.Integer(), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['author_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    op.drop_table('support_messages')
    op.drop_table('action_requests')
    op.drop_table('subscriptions')

    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('server_id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('billing_period', sa.String(), nullable=False),
    sa.Column('next_billing_date', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('action_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('server_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('users', sa.Column('name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(), nullable=False, server_default='active'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'status')
    op.drop_column('users', 'name')

    op.drop_table('action_requests')
    op.drop_table('subscriptions')
    op.drop_table('ticket_messages')
    op.drop_table('support_tickets')
    op.drop_table('notifications')
    op.drop_table('servers')
    op.drop_table('orders')

    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=True),
    sa.Column('plan_name', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('payment_method', sa.String(), nullable=True),
    sa.Column('contact_note', sa.Text(), nullable=True),
    sa.Column('connection_info', sa.Text(), nullable=True),
    sa.Column('expires_at', sa.String(), nullable=True),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('action_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subscription_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('support_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('contact', sa.String(), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
