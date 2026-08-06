"""rbac_and_private_channels

Revision ID: b5eb2c27aba7
Revises: 2865661d362e
Create Date: 2026-08-03 19:37:11.678496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5eb2c27aba7'
down_revision: Union[str, Sequence[str], None] = '2865661d362e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('channel_memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('channel_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_channel_membership_channel_id', 'channel_memberships', ['channel_id'], unique=False)
    op.create_index('ix_channel_membership_user_channel', 'channel_memberships', ['user_id', 'channel_id'], unique=False)
    op.create_index('ix_channel_membership_user_id', 'channel_memberships', ['user_id'], unique=False)
    op.add_column('channels', sa.Column('is_private', sa.Boolean(), server_default='false', nullable=False))
    
    op.execute('DROP INDEX IF EXISTS ix_messages_room_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_messages_room_id;')
    op.execute('DROP INDEX IF EXISTS ix_messages_workspace_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_messages_workspace_id;')
    op.create_index('ix_messages_workspace_created_at', 'messages', ['workspace_id', 'created_at'], unique=False)
    op.create_index('ix_messages_workspace_id', 'messages', ['workspace_id'], unique=False)
    
    op.add_column('organizations', sa.Column('allow_private_channels', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('organizations', sa.Column('allow_public_workspaces', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('users', sa.Column('is_system_admin', sa.Boolean(), server_default='false', nullable=False))
    
    op.execute('DROP INDEX IF EXISTS ix_room_membership_room_id;')
    op.execute('DROP INDEX IF EXISTS ix_room_membership_user_id;')
    op.execute('DROP INDEX IF EXISTS ix_room_membership_user_room;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_membership_user_id;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_membership_user_workspace;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_membership_workspace_id;')
    op.create_index('ix_workspace_membership_user_id', 'workspace_memberships', ['user_id'], unique=False)
    op.create_index('ix_workspace_membership_user_workspace', 'workspace_memberships', ['user_id', 'workspace_id'], unique=False)
    op.create_index('ix_workspace_membership_workspace_id', 'workspace_memberships', ['workspace_id'], unique=False)
    
    op.execute('DROP INDEX IF EXISTS ix_room_memories_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_room_memories_created_by;')
    op.execute('DROP INDEX IF EXISTS ix_room_memories_room_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_room_memories_room_id;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_memories_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_memories_created_by;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_memories_workspace_created_at;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_memories_workspace_id;')
    op.create_index('ix_workspace_memories_created_at', 'workspace_memories', ['created_at'], unique=False)
    op.create_index('ix_workspace_memories_created_by', 'workspace_memories', ['created_by'], unique=False)
    op.create_index('ix_workspace_memories_workspace_created_at', 'workspace_memories', ['workspace_id', 'created_at'], unique=False)
    op.create_index('ix_workspace_memories_workspace_id', 'workspace_memories', ['workspace_id'], unique=False)
    
    op.execute('DROP INDEX IF EXISTS ix_room_tasks_assignee;')
    op.execute('DROP INDEX IF EXISTS ix_room_tasks_room_id;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_tasks_assignee;')
    op.execute('DROP INDEX IF EXISTS ix_workspace_tasks_workspace_id;')
    op.create_index('ix_workspace_tasks_assignee', 'workspace_tasks', ['assignee_username'], unique=False)
    op.create_index('ix_workspace_tasks_workspace_id', 'workspace_tasks', ['workspace_id'], unique=False)


def downgrade() -> None:
    pass
