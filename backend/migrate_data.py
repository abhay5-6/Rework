import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update

from app.db.database import engine
from app.models.user import User
from app.models.room import Room
from app.models.organization import Organization, OrgMembership
from app.models.desk import Desk
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
        
        # 2. Migrate existing rooms to their owner's organization
        rooms_result = await db.execute(select(Room).where(Room.organization_id == None))
        rooms = rooms_result.scalars().all()
        
        for room in rooms:
            if room.owner_id in user_orgs:
                room.organization_id = user_orgs[room.owner_id]
                print(f"Assigned room '{room.name}' to org {user_orgs[room.owner_id]}")
        
        await db.commit()
        
        # 3. Ensure every room has a 'general' desk
        all_rooms_result = await db.execute(select(Room))
        all_rooms = all_rooms_result.scalars().all()
        
        room_default_desks = {}
        for room in all_rooms:
            desk_result = await db.execute(
                select(Desk).where(Desk.room_id == room.id, Desk.name == "general")
            )
            desk = desk_result.scalars().first()
            
            if not desk:
                desk = Desk(name="general", description="General discussion", room_id=room.id)
                db.add(desk)
                await db.flush()
                print(f"Created 'general' desk for room '{room.name}'")
                
            room_default_desks[room.id] = desk.id
            
        await db.commit()
        
        # 4. Migrate existing messages to the default desk of their room
        messages_result = await db.execute(select(Message).where(Message.desk_id == None))
        messages = messages_result.scalars().all()
        
        count = 0
        for msg in messages:
            if msg.room_id in room_default_desks:
                msg.desk_id = room_default_desks[msg.room_id]
                count += 1
                
        if count > 0:
            print(f"Migrated {count} messages to their respective default desks.")
            
        await db.commit()
        print("Data migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate_data())
