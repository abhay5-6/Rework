from sqlalchemy import (
    select,
    or_
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.user import User

from app.models.collaborator_request import (
    CollaboratorRequest
)


async def send_collaboration_request(
    db: AsyncSession,
    sender: User,
    receiver_id: int
):

    if sender.id == receiver_id:

        return "cannot_add_self"

    receiver_result = await db.execute(

        select(User).where(
            User.id == receiver_id
        )
    )

    receiver = (
        receiver_result.scalar()
    )

    if not receiver:

        return "user_not_found"

    existing_result = await db.execute(

        select(CollaboratorRequest).where(

            or_(

                (
                    CollaboratorRequest.sender_id
                        == sender.id
                )
                &
                (
                    CollaboratorRequest.receiver_id
                        == receiver_id
                ),

                (
                    CollaboratorRequest.sender_id
                        == receiver_id
                )
                &
                (
                    CollaboratorRequest.receiver_id
                        == sender.id
                )
            )
        )
    )

    existing = (
        existing_result.scalar()
    )

    if existing:

        return "already_exists"

    request = CollaboratorRequest(

        sender_id=sender.id,

        receiver_id=receiver_id,

        status="pending"
    )

    db.add(request)

    await db.flush()

    return "request_sent"


async def get_pending_collaboration_requests(
    db: AsyncSession,
    current_user: User
):

    result = await db.execute(

        select(
            CollaboratorRequest,
            User
        )
        .join(
            User,
            CollaboratorRequest.sender_id
                == User.id
        )
        .where(
            CollaboratorRequest.receiver_id
                == current_user.id,

            CollaboratorRequest.status
                == "pending"
        )
    )

    requests = result.all()

    formatted_requests = []

    for request, sender in requests:

        formatted_requests.append({

            "request_id":
                request.id,

            "sender_id":
                sender.id,

            "username":
                sender.username
        })

    return formatted_requests


async def accept_collaboration_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):

    result = await db.execute(

        select(CollaboratorRequest).where(

            CollaboratorRequest.id
                == request_id,

            CollaboratorRequest.receiver_id
                == current_user.id
        )
    )

    request = result.scalar()

    if not request:

        return "request_not_found"

    request.status = "accepted"

    await db.flush()

    return "accepted"


async def reject_collaboration_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):

    result = await db.execute(

        select(CollaboratorRequest).where(

            CollaboratorRequest.id
                == request_id,

            CollaboratorRequest.receiver_id
                == current_user.id
        )
    )

    request = result.scalar()

    if not request:

        return "request_not_found"

    request.status = "rejected"

    await db.flush()

    return "rejected"


async def get_collaborators(
    db: AsyncSession,
    current_user: User
):

    result = await db.execute(

        select(
            CollaboratorRequest,
            User
        )
        .join(

            User,

            or_(

                (
                    User.id
                    ==
                    CollaboratorRequest.sender_id
                ),

                (
                    User.id
                    ==
                    CollaboratorRequest.receiver_id
                )
            )
        )
        .where(

            CollaboratorRequest.status
                == "accepted",

            or_(

                CollaboratorRequest.sender_id
                    == current_user.id,

                CollaboratorRequest.receiver_id
                    == current_user.id
            ),

            User.id != current_user.id
        )
    )

    collaborators = result.all()

    formatted = []

    for _, user in collaborators:

        formatted.append({

            "id":
                user.id,

            "username":
                user.username
        })

    return formatted
