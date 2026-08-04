from datetime import timezone
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect
)

import asyncio
import json
import logging
import re
import time

from app.core.config import (
    WEBSOCKET_ALLOWED_ORIGINS,
    settings
)
from app.websocket.manager import manager

from app.websocket.connection import (
    authenticate_websocket
)

from app.db.session import (
    AsyncSessionLocal
)

from sqlalchemy import select
from app.models.workspace import Workspace

from app.services.message_service import (
    create_realtime_message
)

from app.services.ai.auto_memory_service import (
    process_memory_background
)

from app.services.ai.ai_client import (
    generate_workspace_answer,
    generate_web_search_answer
)

router = APIRouter()
logger = logging.getLogger(__name__)


CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_message(text: str) -> str:
    text = text.strip()
    return CONTROL_CHARS_RE.sub("", text)


def is_rate_limited(
    workspace_id: int,
    user_id: int
) -> bool:
    now = time.time()
    user_key = f"{workspace_id}:{user_id}"
    window_seconds = (
        settings.websocket_rate_limit_window_seconds
    )

    timestamps = [
        timestamp
        for timestamp in manager.message_timestamps.get(
            user_key,
            []
        )
        if now - timestamp < window_seconds
    ]

    manager.message_timestamps[user_key] = timestamps

    if len(timestamps) >= (
        settings.websocket_message_rate_limit
    ):
        return True

    timestamps.append(now)
    return False


async def send_error(
    websocket: WebSocket,
    message: str
) -> None:
    await websocket.send_json(
        {
            "type": "error",
            "data": {
                "message": message
            }
        }
    )


@router.websocket("/ws/{workspace_id}")
async def websocket_chat(
    websocket: WebSocket,
    workspace_id: int
):
    origin = websocket.headers.get("origin")

    if origin and settings.app_env != "development":
        allowed_normalized = [o.rstrip("/") for o in WEBSOCKET_ALLOWED_ORIGINS]
        if origin.rstrip("/") not in allowed_normalized:
            logger.warning(
                "websocket_origin_rejected",
                extra={
                    "workspace_id": workspace_id,
                    "origin": origin
                }
            )
            await websocket.close(code=1008)
            return

    token = websocket.query_params.get(
        "token"
    )

    if not token:

        await websocket.close(
            code=1008
        )

        return

    async with AsyncSessionLocal() as db:

        user = await authenticate_websocket(
            token,
            workspace_id,
            db
        )

        if not user:

            await websocket.close(
                code=1008
            )

            return

        await manager.connect(
            workspace_id,
            user.username,
            websocket
        )

        # User joined
        await manager.broadcast(
            workspace_id,
            {
                "type": "online_users",
                "data": {
                    "users":
                        manager.get_online_users(
                            workspace_id
                        )
                }
            }
        )

        try:

            while True:

                try:

                    raw_data = await websocket.receive_text()

                    if len(raw_data) > (
                        settings.websocket_max_message_length
                        + 1000
                    ):
                        await send_error(
                            websocket,
                            "Payload too large"
                        )
                        continue

                    data = json.loads(raw_data)

                except json.JSONDecodeError:
                    await send_error(
                        websocket,
                        "Invalid JSON payload"
                    )
                    continue

                except RuntimeError:

                    break

                if not isinstance(data, dict):
                    await send_error(
                        websocket,
                        "Invalid payload"
                    )
                    continue

                event_type = data.get(
                    "type"
                )

                if event_type == "ping":

                    await websocket.send_json(
                        {
                            "type": "pong"
                        }
                    )

                    continue

                # Typing indicator
                if event_type == "typing":

                    await manager.broadcast(
                        workspace_id,
                        {
                            "type": "typing",
                            "data": {
                                "username":
                                    user.username
                            }
                        }
                    )

                    continue

                # WebRTC Signaling
                if event_type in [
                    "join_call",
                    "leave_call",
                    "webrtc_offer",
                    "webrtc_answer",
                    "webrtc_ice_candidate"
                ]:
                    inner_data = data.get("data", {})
                    
                    logger.info("WebRTC Signaling Received", extra={
                        "event_type": event_type,
                        "sender": user.username,
                        "workspace_id": workspace_id
                    })
                    
                    # Broadcast the signaling message to everyone else in the workspace
                    await manager.broadcast(
                        workspace_id,
                        {
                            "type": event_type,
                            "data": {
                                **inner_data,
                                "sender_username": user.username,
                            }
                        }
                    )
                    continue

                # Chat message
                if event_type == "chat_message":

                    content = data.get("message")
                    extra_data = data.get("extra_data", {})
                    channel_id = data.get("channel_id")
                    temp_id = data.get("temp_id")

                    if not isinstance(content, str):
                        await send_error(websocket, "Message must be text")
                        continue

                    content = sanitize_message(content)

                    if not content and not extra_data:
                        continue

                    if len(content) > (
                        settings.websocket_max_message_length
                    ):
                        await send_error(
                            websocket,
                            "Message too large"
                        )
                        continue

                    if is_rate_limited(
                        workspace_id,
                        user.id
                    ):
                        await send_error(
                            websocket,
                            "Rate limit exceeded"
                        )
                        continue

                    saved_message = await create_realtime_message(
                        db,
                        workspace_id,
                        user,
                        content,
                        extra_data,
                        channel_id
                    )

                    if not saved_message:

                        await websocket.send_json(
                            {
                                "type": "error",
                                "data": {
                                    "message":
                                        "Access denied"
                                }
                            }
                        )

                        continue

                    await db.commit()

                    message_payload = {
                        "type": "chat_message",
                        "data": {
                            "id":
                                saved_message.id,

                            "user_id":
                                user.id,

                            "username":
                                user.username,

                            "workspace_id": workspace_id,
                            "channel_id": saved_message.channel_id,
                            "parent_id": getattr(saved_message, 'parent_id', None),
                            "message": saved_message.content,
                            "extra_data": saved_message.extra_data,
                            "created_at": saved_message.created_at.replace(tzinfo=timezone.utc).isoformat(),
                            "edited_at": None,
                            "temp_id": temp_id
                        }
                    }

                    await manager.broadcast(
                        workspace_id,
                        message_payload
                    )

                    # Process AI memory in background if enabled
                    workspace_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
                    workspace = workspace_result.scalar()
                    
                    if workspace and workspace.ai_enabled:
                        try:
                            print("Scheduling memory extraction task")
                            asyncio.create_task(
                                process_memory_background(
                                    workspace_id,
                                    user.id,
                                    saved_message.id,
                                    saved_message.content
                                )
                            )
                        except Exception:
                            print("Failed to schedule memory extraction task")
                            logger.exception(
                                "memory_background_task_create_failed",
                                extra={
                                    "workspace_id": workspace_id,
                                    "user_id": user.id
                                }
                            )
                            
                    # Trigger AI chat commands if applicable
                    is_web_query = content.startswith("@web")
                    is_ai_query = content.startswith("@ai")

                    if is_web_query or is_ai_query:
                        query_text = content[4:].strip() if is_web_query else content[3:].strip()
                        if query_text:
                            asyncio.create_task(
                                handle_ai_chat_command(
                                    workspace_id,
                                    query_text,
                                    is_web_query
                                )
                            )

                    continue

                await send_error(
                    websocket,
                    "Unsupported event type"
                )

        except WebSocketDisconnect:

            pass

        except Exception:

            logger.exception(
                "websocket_chat_failed",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user.id
                }
            )

            try:
                await websocket.close(
                    code=1011
                )
            except Exception:
                pass

        finally:

            manager.disconnect(
                workspace_id,
                user.username,
                websocket
            )

            await manager.broadcast(
                workspace_id,
                {
                    "type": "online_users",
                    "data": {
                        "users":
                            manager.get_online_users(
                                workspace_id
                            )
                    }
                }
            )

async def handle_ai_chat_command(
    workspace_id: int,
    query: str,
    is_web_query: bool
):
    try:
        async with AsyncSessionLocal() as db:
            if is_web_query:
                answer = await generate_web_search_answer(query)
            else:
                answer = await generate_workspace_answer(db, workspace_id, query)
                
            if answer:
                saved_message = await create_realtime_message(
                    db,
                    workspace_id,
                    user=None,
                    content=answer
                )
                
                if saved_message:
                    message_payload = {
                        "type": "chat_message",
                        "data": {
                            "id": saved_message.id,
                            "user_id": None,
                            "username": "Rework AI",
                            "workspace_id": workspace_id,
                            "channel_id": saved_message.channel_id,
                            "parent_id": getattr(saved_message, 'parent_id', None),
                            "message": saved_message.content,
                            "created_at": saved_message.created_at.replace(tzinfo=timezone.utc).isoformat(),
                            "edited_at": None
                        }
                    }
                    await manager.broadcast(workspace_id, message_payload)
    except Exception:
        logger.exception(
            "ai_chat_command_failed",
            extra={"workspace_id": workspace_id, "query": query, "is_web": is_web_query}
        )
