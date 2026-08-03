from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.message import Message
from app.schemas.message import MessageCreate
from app.repositories.base import BaseRepository

class MessageUpdate(BaseModel):
    pass

class MessageRepository(BaseRepository[Message, Dict[str, Any], MessageUpdate]):
    async def get_messages_for_room(
        self, db: AsyncSession, *, room_id: int, desk_id: Optional[int] = None, skip: int = 0, limit: int = 50
    ):
        from app.models.user import User
        
        query = (
            select(Message, User.username)
            .outerjoin(User, Message.sender_id == User.id)
            .where(Message.room_id == room_id)
        )
        
        if desk_id is not None:
            query = query.where(Message.desk_id == desk_id)
            
        query = query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.all()


message_repo = MessageRepository(Message)
