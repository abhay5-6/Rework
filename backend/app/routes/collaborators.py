from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.db.session import get_db

from app.core.dependencies import (
    get_current_user
)

from app.models.user import User

from app.services.collaborator_service import (

    send_collaboration_request,

    get_pending_collaboration_requests,

    accept_collaboration_request,

    reject_collaboration_request,

    get_collaborators
)
from app.schemas.common import (
    CollaboratorRequestResponse,
    CollaboratorResponse,
    MessageOnlyResponse,
)

router = APIRouter(

    prefix="/collaborators",

    tags=["Collaborators"]
)


@router.post("/request/{user_id}", response_model=MessageOnlyResponse)
async def send_request(

    user_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = (
        await send_collaboration_request(
            db,
            current_user,
            user_id
        )
    )

    if result == "cannot_add_self":

        raise HTTPException(
            status_code=400,
            detail="Cannot collaborate with yourself"
        )

    if result == "user_not_found":

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if result == "already_exists":

        raise HTTPException(
            status_code=400,
            detail="Request already exists"
        )

    await db.commit()

    return {
        "message":
            "Collaboration request sent"
    }


@router.get("/requests", response_model=list[CollaboratorRequestResponse])
async def pending_requests(

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    requests = (
        await get_pending_collaboration_requests(
            db,
            current_user
        )
    )

    return requests


@router.post(
    "/requests/{request_id}/accept",
    response_model=MessageOnlyResponse
)
async def accept_request(

    request_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = (
        await accept_collaboration_request(
            db,
            request_id,
            current_user
        )
    )

    if result == "request_not_found":

        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    await db.commit()

    return {
        "message":
            "Collaboration accepted"
    }


@router.post(
    "/requests/{request_id}/reject",
    response_model=MessageOnlyResponse
)
async def reject_request(

    request_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = (
        await reject_collaboration_request(
            db,
            request_id,
            current_user
        )
    )

    if result == "request_not_found":

        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    await db.commit()

    return {
        "message":
            "Collaboration rejected"
    }


@router.get("/", response_model=list[CollaboratorResponse])
async def list_collaborators(

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    collaborators = (
        await get_collaborators(
            db,
            current_user
        )
    )

    return collaborators
