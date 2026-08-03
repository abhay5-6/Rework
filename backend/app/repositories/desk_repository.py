from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.desk import Desk
from app.schemas.desk import DeskCreate
from app.repositories.base import BaseRepository

class DeskUpdate(BaseModel):
    pass

class DeskRepository(BaseRepository[Desk, DeskCreate, DeskUpdate]):
    async def get_desks_for_room(self, db: AsyncSession, *, room_id: int) -> List[Desk]:
        query = select(Desk).where(Desk.room_id == room_id)
        result = await db.execute(query)
        return list(result.scalars().all())

desk_repo = DeskRepository(Desk)
