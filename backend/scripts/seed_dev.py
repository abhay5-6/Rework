import asyncio
import os
import sys

# Add backend directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.channel import Channel
from app.models.membership import WorkspaceMembership, ChannelMembership
from app.core.security import hash_password

async def seed():
    async with AsyncSessionLocal() as session:
        # Create users
        users_data = [
            {"username": "admin", "email": "admin@rework.com", "is_system_admin": True},
            {"username": "alice", "email": "alice@rework.com", "is_system_admin": False},
            {"username": "bob", "email": "bob@rework.com", "is_system_admin": False},
        ]
        
        users = {}
        for u_data in users_data:
            result = await session.execute(select(User).where(User.email == u_data["email"]))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    username=u_data["username"],
                    email=u_data["email"],
                    hashed_password=hash_password("password123"),
                    email_verified=True,
                    is_system_admin=u_data["is_system_admin"]
                )
                session.add(user)
                await session.flush()
                print(f"Created user: {user.email}")
            users[u_data["username"]] = user

        # Create Organization
        result = await session.execute(select(Organization).where(Organization.name == "Acme Corp"))
        org = result.scalar_one_or_none()
        if not org:
            org = Organization(
                name="Acme Corp",
                description="A test organization for development",
                owner_id=users["admin"].id
            )
            session.add(org)
            await session.flush()
            print("Created Organization: Acme Corp")

        # Create Workspace
        result = await session.execute(select(Workspace).where(Workspace.name == "Engineering"))
        workspace = result.scalar_one_or_none()
        if not workspace:
            workspace = Workspace(
                name="Engineering",
                description="Engineering team workspace",
                owner_id=users["admin"].id,
                organization_id=org.id,
                is_private=False
            )
            session.add(workspace)
            await session.flush()
            print("Created Workspace: Engineering")

            # Add users to workspace
            for user in users.values():
                membership = WorkspaceMembership(
                    user_id=user.id,
                    workspace_id=workspace.id,
                    role="owner" if user.username == "admin" else "member"
                )
                session.add(membership)
            await session.flush()

        # Create Channels
        channels_data = [
            {"name": "general", "is_private": False},
            {"name": "backend", "is_private": False},
            {"name": "frontend", "is_private": False},
            {"name": "top-secret", "is_private": True},
        ]

        for c_data in channels_data:
            result = await session.execute(
                select(Channel).where(Channel.name == c_data["name"]).where(Channel.workspace_id == workspace.id)
            )
            channel = result.scalar_one_or_none()
            if not channel:
                channel = Channel(
                    name=c_data["name"],
                    description=f"{c_data['name']} channel",
                    workspace_id=workspace.id,
                    owner_id=users["admin"].id,
                    is_private=c_data["is_private"]
                )
                session.add(channel)
                await session.flush()
                print(f"Created Channel: {channel.name}")

                # Add users to channel
                for user in users.values():
                    if c_data["is_private"] and user.username == "bob":
                        continue # bob is not in top-secret
                    c_membership = ChannelMembership(
                        user_id=user.id,
                        channel_id=channel.id,
                        role="owner" if user.username == "admin" else "member"
                    )
                    session.add(c_membership)
                await session.flush()

        await session.commit()
        print("Dev environment seeded successfully! (Password for all users: 'password123')")

if __name__ == "__main__":
    asyncio.run(seed())
