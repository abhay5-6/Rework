from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.channel import Channel
from app.schemas.channel import ChannelCreate
from app.repositories.base import BaseRepository

class ChannelUpdate(BaseModel):
    pass

class ChannelRepository(BaseRepository[Channel, ChannelCreate, ChannelUpdate]):
    async def get_channels_for_workspace(self, db: AsyncSession, *, workspace_id: int) -> List[Channel]:
        query = select(Channel).where(Channel.workspace_id == workspace_id)
        result = await db.execute(query)
        return list(result.scalars().all())

channel_repo = ChannelRepository(Channel)
