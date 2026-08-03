from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.join_request import RoomJoinRequest
from app.repositories.base import BaseRepository


class JoinRequestRepository(BaseRepository[RoomJoinRequest, Dict[str, Any], Dict[str, Any]]):
    async def get_join_request(self, db: AsyncSession, *, workspace_id: int, user_id: int) -> Optional[RoomJoinRequest]:
        query = select(RoomJoinRequest).where(
            RoomJoinRequest.workspace_id == workspace_id,
            RoomJoinRequest.user_id == user_id,
            RoomJoinRequest.status == "pending"
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_workspace_requests(self, db: AsyncSession, *, workspace_id: int) -> List[RoomJoinRequest]:
        query = select(RoomJoinRequest).where(
            RoomJoinRequest.workspace_id == workspace_id,
            RoomJoinRequest.status == "pending"
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_pending_requests_with_details(self, db: AsyncSession, *, owned_workspace_ids: List[int]):
        from app.models.workspace import Workspace
        from app.models.user import User
        query = (
            select(RoomJoinRequest, Workspace, User)
            .join(Workspace, RoomJoinRequest.workspace_id == Workspace.id)
            .join(User, RoomJoinRequest.user_id == User.id)
            .where(
                RoomJoinRequest.workspace_id.in_(owned_workspace_ids),
                RoomJoinRequest.status == "pending"
            )
        )
        result = await db.execute(query)
        return result.all()


join_request_repo = JoinRequestRepository(RoomJoinRequest)
