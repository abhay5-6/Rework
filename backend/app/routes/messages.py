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
    get_workspace_messages
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces",
    tags=["Messages"]
)
from app.services.ai.auto_memory_service import (
    process_memory_background
)
from fastapi import BackgroundTasks

from arq import ArqRedis
from app.core.dependencies import get_arq_pool

@router.post(
    "/{workspace_id}/messages",
    response_model=MessageResponse
)
@limiter.limit(settings.message_rate_limit)
async def create_message(

    request: Request,

    workspace_id: int,

    message: MessageCreate,

    arq_pool: ArqRedis = Depends(get_arq_pool),

    db: AsyncSession = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    created_message = await send_message(

        db,

        workspace_id,

        current_user,

        message
    )

    if not created_message:

        raise HTTPException(

            status_code=403,

            detail=(
                "You are not a member "
                "of this workspace"
            )
        )

    await db.commit()

    if arq_pool:
        await arq_pool.enqueue_job(
            "run_process_memory_background",
            workspace_id,
            current_user.id,
            created_message.id,
            created_message.content
        )
    else:
        # Fallback if ARQ is not running (e.g. testing)
        import asyncio
        asyncio.create_task(
            process_memory_background(
                workspace_id,
                current_user.id,
                message_id=created_message.id,
                message_content=created_message.content
            )
        )

    return created_message
@router.get(
    "/{workspace_id}/messages",
    response_model=list[MessageResponse]
)
async def list_workspace_messages(
    workspace_id: int,
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
    messages = await get_workspace_messages(
        db,
        workspace_id,
        current_user,
        limit,
        offset
    )

    if messages is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this workspace"
        )

    return messages

from app.schemas.message import MessageUpdate, MessageMove
from app.services.message_service import update_message, move_message

from app.websocket.manager import manager

@router.put(
    "/{workspace_id}/messages/{message_id}",
    response_model=MessageResponse
)
async def edit_message(
    workspace_id: int,
    message_id: int,
    message_data: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message = await update_message(db, message_id, current_user, message_data.content)
    if not message:
        raise HTTPException(status_code=403, detail="Not authorized to edit this message")
    
    await db.commit()
    
    await manager.broadcast(
        workspace_id,
        {
            "type": "message_updated",
            "message_id": message.id,
            "content": message.content,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None
        }
    )
    
    return message


@router.patch(
    "/{workspace_id}/messages/{message_id}/move",
    response_model=MessageResponse
)
async def move_message_route(
    workspace_id: int,
    message_id: int,
    message_data: MessageMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message = await move_message(db, message_id, current_user, message_data.channel_id)
    if not message:
        raise HTTPException(status_code=403, detail="Not authorized to move this message")
        
    await db.commit()
    
    await manager.broadcast(
        workspace_id,
        {
            "type": "message_moved",
            "message_id": message.id,
            "new_channel_id": message.channel_id
        }
    )
    
    return message
