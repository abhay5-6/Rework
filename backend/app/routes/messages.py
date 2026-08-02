from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.message import (
    MessageCreate,
    MessageResponse
)
from app.services.message_service import (
    send_message,
    get_room_messages
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rooms",
    tags=["Messages"]
)
from app.services.ai.auto_memory_service import (
    process_memory_background
)
from fastapi import BackgroundTasks

@router.post(
    "/{room_id}/messages",
    response_model=MessageResponse
)
@limiter.limit(settings.message_rate_limit)
async def create_message(

    request: Request,

    room_id: int,

    message: MessageCreate,

    background_tasks: BackgroundTasks,

    db: AsyncSession = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    created_message = await send_message(

        db,

        room_id,

        current_user,

        message
    )

    if not created_message:

        raise HTTPException(

            status_code=403,

            detail=(
                "You are not a member "
                "of this room"
            )
        )

    await db.commit()

    background_tasks.add_task(

        process_memory_background,

        room_id,

        current_user.id,

        message_id=created_message.id,

        message_content=created_message.content
    )

    return created_message
@router.get(
    "/{room_id}/messages",
    response_model=list[MessageResponse]
)
async def list_room_messages(
    room_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = await get_room_messages(
        db,
        room_id,
        current_user,
        limit,
        offset
    )

    if messages is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this room"
        )

    return messages
