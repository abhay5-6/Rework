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
    # Rename tables safely if they exist
    op.execute('ALTER TABLE IF EXISTS rooms RENAME TO workspaces;')
    op.execute('ALTER TABLE IF EXISTS desks RENAME TO channels;')
    op.execute('ALTER TABLE IF EXISTS room_memories RENAME TO workspace_memories;')
    op.execute('ALTER TABLE IF EXISTS room_tasks RENAME TO workspace_tasks;')
    op.execute('ALTER TABLE IF EXISTS room_join_requests RENAME TO workspace_join_requests;')
    op.execute('ALTER TABLE IF EXISTS room_memberships RENAME TO workspace_memberships;')
    
    # Rename columns safely if old column names exist
    op.execute("""
        DO $$ 
        BEGIN 
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='room_id') THEN
                ALTER TABLE channels RENAME COLUMN room_id TO workspace_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='room_id') THEN
                ALTER TABLE messages RENAME COLUMN room_id TO workspace_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='desk_id') THEN
                ALTER TABLE messages RENAME COLUMN desk_id TO channel_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workspace_memories' AND column_name='room_id') THEN
                ALTER TABLE workspace_memories RENAME COLUMN room_id TO workspace_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workspace_tasks' AND column_name='room_id') THEN
                ALTER TABLE workspace_tasks RENAME COLUMN room_id TO workspace_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workspace_join_requests' AND column_name='room_id') THEN
                ALTER TABLE workspace_join_requests RENAME COLUMN room_id TO workspace_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workspace_memberships' AND column_name='room_id') THEN
                ALTER TABLE workspace_memberships RENAME COLUMN room_id TO workspace_id;
            END IF;
        END $$;
    """)
    
    # Rename indexes if they exist
    op.execute('ALTER INDEX IF EXISTS ix_rooms_id RENAME TO ix_workspaces_id;')
    op.execute('ALTER INDEX IF EXISTS ix_desks_id RENAME TO ix_channels_id;')
    op.execute('ALTER INDEX IF EXISTS ix_desks_room_id RENAME TO ix_channels_workspace_id;')

def downgrade() -> None:
    pass
