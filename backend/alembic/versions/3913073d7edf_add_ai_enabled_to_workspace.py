"""add ai_enabled to workspace

Revision ID: 3913073d7edf
Revises: 9f4c2d1a7b11
Create Date: 2026-06-26 17:14:08.554236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3913073d7edf'
down_revision: Union[str, Sequence[str], None] = '9f4c2d1a7b11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workspaces', sa.Column('ai_enabled', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('workspaces', 'ai_enabled')
