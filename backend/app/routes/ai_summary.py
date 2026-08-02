from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.db.session import get_db

from app.core.dependencies import (
    get_current_user
)
from app.core.config import settings
from app.core.rate_limit import limiter

from app.models.user import User

from app.services.ai.memory_summary_service import (
    generate_memory_summary
)

from app.services.message_service import has_room_access
from app.schemas.common import MemorySummaryResponse

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.get("/summary/{room_id}", response_model=MemorySummaryResponse)
@limiter.limit(settings.ai_rate_limit)

async def summarize_room_memory(
    request: Request,

    room_id: int,

    query: str,

    db: AsyncSession = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    # Verify user has access to room
    has_access = await has_room_access(
        db,
        room_id,
        current_user
    )

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this room"
        )

    summary = await (
        generate_memory_summary(

            db,

            room_id,

            query,

            current_user.id
        )
    )

    return {
        "summary": summary
    }
