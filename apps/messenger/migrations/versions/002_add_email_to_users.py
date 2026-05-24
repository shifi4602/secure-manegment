"""Add email column to users

Revision ID: 002
Revises: 001
Create Date: 2026-05-14

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXERCISE  (from MIGRATIONS.md)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The User model in server/models.py now has an `email` column:

      email: Mapped[str | None] = mapped_column(String(100), nullable=True)

  Your job is to write upgrade() and downgrade() so that:

    alembic upgrade head    → adds the column to the live database
    alembic downgrade -1    → removes it (rolls back safely)

  See MIGRATIONS.md → "Exercise: Add email to User" for the full
  step-by-step walkthrough and the exact op calls to use.

WHY nullable=True?
  Existing rows have no email value — they were inserted before this
  column existed.  A NOT NULL column with no default would fail when
  Alembic tries to back-fill those rows.  nullable=True lets existing
  rows keep NULL until the application fills them in.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# TODO — add the email column in upgrade(), remove it in downgrade()
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """
    Add a nullable `email` column to the `users` table.

    Hint:
        op.add_column(
            "users",
            sa.Column("email", sa.String(100), nullable=True),
        )
    """
    raise NotImplementedError("Implement upgrade: add email column to users")


def downgrade() -> None:
    """
    Remove the `email` column (undoes upgrade).

    Hint:
        op.drop_column("users", "email")
    """
    raise NotImplementedError("Implement downgrade: drop email column from users")
