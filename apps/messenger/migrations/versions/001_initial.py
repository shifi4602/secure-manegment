"""Create users and messages tables

Revision ID: 001
Revises:
Create Date: 2026-05-14

╔══════════════════════════════════════════════════════════════╗
║  THIS FILE IS COMPLETE — you do not need to change anything. ║
╚══════════════════════════════════════════════════════════════╝

Run:  alembic upgrade head
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",            sa.Integer,                  primary_key=True),
        sa.Column("username",      sa.String(50),               nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255),              nullable=False),
        sa.Column("created_at",    sa.DateTime(timezone=True),  nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "messages",
        sa.Column("id",         sa.Integer,                 primary_key=True),
        sa.Column("sender",     sa.String(50),              nullable=False),
        sa.Column("recipient",  sa.String(50),              nullable=False),
        sa.Column("ciphertext", sa.Text,                    nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_sender",    "messages", ["sender"])
    op.create_index("ix_messages_recipient", "messages", ["recipient"])


def downgrade() -> None:
    op.drop_index("ix_messages_recipient", table_name="messages")
    op.drop_index("ix_messages_sender",    table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
