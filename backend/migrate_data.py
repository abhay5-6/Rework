import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update

from app.db.database import engine
from app.models.user import User
from app.models.workspace import Workspace
from app.models.organization import Organization, OrgMembership
from app.models.channel import Channel
from app.models.message import Message

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def migrate_data():
    async with AsyncSessionLocal() as db:
        print("Starting data migration...")
        
        # 1. Ensure every user has a personal organization
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        
        user_orgs = {}
        for user in users:
            # Check if user already has an org they own
            org_result = await db.execute(
                select(Organization).where(Organization.created_by == user.id)
            )
            org = org_result.scalars().first()
            
            if not org:
                # Create default org
                org_name = f"{user.username}'s Org"
                org = Organization(name=org_name, created_by=user.id)
                db.add(org)
                await db.flush()
                
                # Create owner membership
                membership = OrgMembership(org_id=org.id, user_id=user.id, role="owner")
                db.add(membership)
                print(f"Created personal org for user {user.username}")
            
            user_orgs[user.id] = org.id
            
        await db.commit()
        
        # 2. Migrate existing workspaces to their owner's organization
        rooms_result = await db.execute(select(Workspace).where(Workspace.organization_id == None))
        workspaces = rooms_result.scalars().all()
        
        for workspace in workspaces:
            if workspace.owner_id in user_orgs:
                workspace.organization_id = user_orgs[workspace.owner_id]
                print(f"Assigned workspace '{workspace.name}' to org {user_orgs[workspace.owner_id]}")
        
        await db.commit()
        
        # 3. Ensure every workspace has a 'general' channel
        all_workspaces_result = await db.execute(select(Workspace))
        all_workspaces = all_workspaces_result.scalars().all()
        
        workspace_default_channels = {}
        for workspace in all_workspaces:
            channel_result = await db.execute(
                select(Channel).where(Channel.workspace_id == workspace.id, Channel.name == "general")
            )
            channel = channel_result.scalars().first()
            
            if not channel:
                channel = Channel(name="general", description="General discussion", workspace_id=workspace.id)
                db.add(channel)
                await db.flush()
                print(f"Created 'general' channel for workspace '{workspace.name}'")
                
            workspace_default_channels[workspace.id] = channel.id
            
        await db.commit()
        
        # 4. Migrate existing messages to the default channel of their workspace
        messages_result = await db.execute(select(Message).where(Message.channel_id == None))
        messages = messages_result.scalars().all()
        
        count = 0
        for msg in messages:
            if msg.workspace_id in workspace_default_channels:
                msg.channel_id = workspace_default_channels[msg.workspace_id]
                count += 1
                
        if count > 0:
            print(f"Migrated {count} messages to their respective default channels.")
            
        await db.commit()
        print("Data migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate_data())
