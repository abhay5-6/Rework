"""rename_tables_and_columns

Revision ID: 2865661d362e
Revises: 01115320d056
Create Date: 2026-08-03 19:06:59.756325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2865661d362e'
down_revision: Union[str, Sequence[str], None] = '01115320d056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.execute('ALTER TABLE rooms RENAME TO workspaces;')
    op.execute('ALTER TABLE desks RENAME TO channels;')
    op.execute('ALTER TABLE room_memories RENAME TO workspace_memories;')
    op.execute('ALTER TABLE room_tasks RENAME TO workspace_tasks;')
    op.execute('ALTER TABLE room_join_requests RENAME TO workspace_join_requests;')
    op.execute('ALTER TABLE room_memberships RENAME TO workspace_memberships;')
    
    # Rename columns in workspaces/channels
    op.execute('ALTER TABLE channels RENAME COLUMN room_id TO workspace_id;')
    
    # Rename columns in related tables
    op.execute('ALTER TABLE messages RENAME COLUMN room_id TO workspace_id;')
    op.execute('ALTER TABLE messages RENAME COLUMN desk_id TO channel_id;')
    op.execute('ALTER TABLE workspace_memories RENAME COLUMN room_id TO workspace_id;')
    op.execute('ALTER TABLE workspace_tasks RENAME COLUMN room_id TO workspace_id;')
    op.execute('ALTER TABLE workspace_join_requests RENAME COLUMN room_id TO workspace_id;')
    op.execute('ALTER TABLE workspace_memberships RENAME COLUMN room_id TO workspace_id;')
    
    # Rename indexes to match (optional but good practice)
    # The indexes will still work even if not renamed, but let's rename them if they exist
    op.execute('ALTER INDEX IF EXISTS ix_rooms_id RENAME TO ix_workspaces_id;')
    op.execute('ALTER INDEX IF EXISTS ix_desks_id RENAME TO ix_channels_id;')
    op.execute('ALTER INDEX IF EXISTS ix_desks_room_id RENAME TO ix_channels_workspace_id;')

def downgrade() -> None:
    # Revert columns in related tables
    op.execute('ALTER TABLE workspace_memberships RENAME COLUMN workspace_id TO room_id;')
    op.execute('ALTER TABLE workspace_join_requests RENAME COLUMN workspace_id TO room_id;')
    op.execute('ALTER TABLE workspace_tasks RENAME COLUMN workspace_id TO room_id;')
    op.execute('ALTER TABLE workspace_memories RENAME COLUMN workspace_id TO room_id;')
    op.execute('ALTER TABLE messages RENAME COLUMN channel_id TO desk_id;')
    op.execute('ALTER TABLE messages RENAME COLUMN workspace_id TO room_id;')
    
    # Revert columns in workspaces/channels
    op.execute('ALTER TABLE channels RENAME COLUMN workspace_id TO room_id;')
    
    # Revert table names
    op.execute('ALTER TABLE workspace_memberships RENAME TO room_memberships;')
    op.execute('ALTER TABLE workspace_join_requests RENAME TO room_join_requests;')
    op.execute('ALTER TABLE workspace_tasks RENAME TO room_tasks;')
    op.execute('ALTER TABLE workspace_memories RENAME TO room_memories;')
    op.execute('ALTER TABLE channels RENAME TO desks;')
    op.execute('ALTER TABLE workspaces RENAME TO rooms;')
