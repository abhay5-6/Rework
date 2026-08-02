from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.db.session import (
    get_db
)

from app.services.ai.graph_service import (
    build_room_graph
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.message_service import has_room_access
from app.schemas.common import RoomGraphResponse


router = APIRouter(

    prefix="/ai",

    tags=["AI Graph"]
)


@router.get(
    "/graph/{room_id}",
    response_model=RoomGraphResponse
)
@limiter.limit(settings.ai_rate_limit)
async def get_room_graph(
    request: Request,

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

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
    

    graph = await (
        build_room_graph(
            db,
            room_id
        )
    )

    return graph
