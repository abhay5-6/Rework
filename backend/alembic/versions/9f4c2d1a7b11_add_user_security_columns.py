"""add user security columns

Revision ID: 9f4c2d1a7b11
Revises: e35ba8a81041
Create Date: 2026-06-20 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f4c2d1a7b11"
down_revision: Union[str, Sequence[str], None] = "e35ba8a81041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new auth/security columns to users table.
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_token",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_token",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_expires_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "created_at")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")
