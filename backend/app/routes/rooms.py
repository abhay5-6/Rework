from app.utils.permissions import (
    require_room_admin,
    require_room_owner,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.db.session import get_db

from app.schemas.room import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    RoomMemberResponse
)

from app.services.room_service import (
    create_room,
    get_rooms,
    get_room_by_id,
    join_room,
    leave_room,
    delete_room,
    toggle_room_ai
)

from app.services.membership_service import (
    get_room_members,
    promote_member,
    demote_member,
    remove_member
)
from app.services.join_request_service import (
    get_pending_requests,
    approve_join_request,
    reject_join_request,
)

from app.core.dependencies import (
    get_current_user
)

from app.models.user import User
from app.schemas.common import (
    MessageOnlyResponse,
    RoomJoinRequestResponse,
    RoomListResponse,
    RoomUpdateResponse,
    SuccessMessageResponse,
)
from app.core.exceptions import (
    AlreadyMemberException,
    JoinRequestNotFoundException,
    RoomAlreadyExistsException,
    RoomAlreadyJoinedException,
    RoomJoinRequestPendingException,
    RoomMembershipRequiredException,
    RoomNotFoundException,
    RoomOwnerCannotLeaveException,
    RoomOwnerRequiredException,
)

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post(
    "/",
    response_model=RoomResponse
)
async def create_new_room(
    room: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        created_room = await create_room(
            db,
            room,
            current_user
        )
        return {
            "id": created_room.id,
            "name": created_room.name,
            "description": created_room.description,
            "is_private": created_room.is_private,
            "is_member": True,
            "role": "owner",
            "owner_id": current_user.id
        }
    except RoomAlreadyExistsException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=RoomListResponse
)
async def list_rooms(
    skip: int = 0,
    limit: int = 10,
    organization_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    # Validate pagination parameters
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 10
    if limit > 100:  # Max 100 rooms per page
        limit = 100

    result = await get_rooms(
        db,
        current_user,
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )

    return {
        "items": result["items"],
        "total": result["total"],
        "skip": skip,
        "limit": limit
    }


@router.get("/join-requests", response_model=list[RoomJoinRequestResponse])
async def list_pending_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requests = await get_pending_requests(db, current_user)
    return requests

@router.post(
    "/join-requests/{request_id}/approve",
    response_model=MessageOnlyResponse
)
async def approve_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        await approve_join_request(db, request_id, current_user)
        return {"message": "Request approved"}
    except (
        JoinRequestNotFoundException,
        RoomOwnerRequiredException,
        AlreadyMemberException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post(
    "/join-requests/{request_id}/reject",
    response_model=MessageOnlyResponse
)
async def reject_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        await reject_join_request(db, request_id, current_user)
        return {"message": "Request rejected"}
    except (
        JoinRequestNotFoundException,
        RoomOwnerRequiredException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get(
    "/{room_id}",
    response_model=RoomResponse
)
async def get_room(

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):
    room = await get_room_by_id(db, room_id, current_user)
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )
    return room


@router.post("/{room_id}/join", response_model=SuccessMessageResponse)
async def join_existing_room(

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):
    try:
        result = await join_room(
            db,
            room_id,
            current_user
        )
        if result == "request_sent":
            return {
                "success": True,
                "message":
                    "Join request sent"
            }

        if result == "joined":
            return {
                "success": True,
                "message":
                    "Joined room successfully"
            }

        raise HTTPException(
            status_code=400,
            detail="Join failed"
        )
    except (
        RoomNotFoundException,
        RoomAlreadyJoinedException,
        RoomJoinRequestPendingException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{room_id}/leave", response_model=MessageOnlyResponse)
async def leave_existing_room(

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):
    try:
        await leave_room(
            db,
            room_id,
            current_user
        )
        return {
            "message":
                "Left room successfully"
        }
    except (
        RoomNotFoundException,
        RoomMembershipRequiredException,
        RoomOwnerCannotLeaveException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/{room_id}",
    response_model=MessageOnlyResponse,
    dependencies=[Depends(require_room_owner)],
)
async def delete_existing_room(

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):
    try:
        await delete_room(
            db,
            room_id,
            current_user
        )
        return {
            "message":
                "Room deleted successfully"
        }
    except (
        RoomNotFoundException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch(
    "/{room_id}",
    response_model=RoomUpdateResponse,
    dependencies=[Depends(require_room_owner)],
)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        await toggle_room_ai(
            db,
            room_id,
            room_data.ai_enabled,
            current_user
        )
        return {
            "message": "Room updated successfully",
            "ai_enabled": room_data.ai_enabled
        }
    except (
        RoomNotFoundException,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# =========================
# MEMBERS / HIERARCHY
# =========================

@router.get(
    "/{room_id}/members",
    response_model=list[
        RoomMemberResponse
    ]
)
async def list_room_members(

    room_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    members = await get_room_members(
        db,
        room_id,
        current_user
    )

    if members is None:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return members


@router.post(
    "/{room_id}/promote/{user_id}",
    response_model=MessageOnlyResponse,
    dependencies=[Depends(require_room_owner)],
)
async def promote_room_member(

    room_id: int,

    user_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = await promote_member(
        db,
        room_id,
        user_id,
        current_user
    )

    if result == "member_not_found":

        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )

    if result == "already_admin":

        raise HTTPException(
            status_code=400,
            detail="User is already admin"
        )

    if result == "cannot_modify_owner":

        raise HTTPException(
            status_code=400,
            detail="Cannot modify owner"
        )

    if result != "promoted":
        raise HTTPException(status_code=400, detail="Promote failed")

    return {
        "message":
            "Member promoted"
    }


@router.post(
    "/{room_id}/demote/{user_id}",
    response_model=MessageOnlyResponse,
    dependencies=[Depends(require_room_owner)],
)
async def demote_room_member(

    room_id: int,

    user_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = await demote_member(
        db,
        room_id,
        user_id,
        current_user
    )

    if result == "member_not_found":

        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )

    if result == "cannot_modify_owner":

        raise HTTPException(
            status_code=400,
            detail="Cannot modify owner"
        )
    
    if result == "cannot_demote_self":

        raise HTTPException(
            status_code=400,
            detail="Owner cannot demote self"
        )
    
    if result == "already_member":

        raise HTTPException(
            status_code=400,
            detail="User is already member"
        )

    if result != "demoted":
        raise HTTPException(status_code=400, detail="Demote failed")

    return {
        "message":
            "Member demoted"
    }


@router.post(
    "/{room_id}/remove/{user_id}",
    response_model=MessageOnlyResponse,
    dependencies=[Depends(require_room_admin)],
)
async def remove_room_member(

    room_id: int,

    user_id: int,

    db: AsyncSession = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    )
):

    result = await remove_member(
        db,
        room_id,
        user_id,
        current_user
    )

    if result == "member_not_found":

        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )

    if result == "cannot_remove_self":

        raise HTTPException(
            status_code=400,
            detail="Cannot remove yourself"
        )
    if result == "cannot_remove_admin":

        raise HTTPException(
            status_code=403,
            detail="Admin cannot remove another admin"
        )

    if result == "cannot_remove_owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot remove owner"
        )

    if result != "removed":
        raise HTTPException(status_code=400, detail="Remove failed")

    return {
        "message":
            "Member removed"
    }