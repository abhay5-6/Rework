from datetime import datetime, timezone
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.room_task import RoomTask
from app.core.dependencies import get_current_user
from app.services.message_service import has_room_access
from app.websocket.manager import manager
from app.schemas.common import RoomTaskResponse

router = APIRouter(prefix="/rooms", tags=["Tasks"])

@router.get("/{room_id}/tasks", response_model=list[RoomTaskResponse])
async def get_room_tasks(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    allowed = await has_room_access(db, room_id, current_user)
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(RoomTask).where(RoomTask.room_id == room_id).order_by(RoomTask.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "description": t.description,
            "assignee_username": t.assignee_username,
            "status": t.status,
            "created_at": t.created_at,
            "completed_at": t.completed_at
        }
        for t in tasks
    ]

@router.patch("/{room_id}/tasks/{task_id}", response_model=RoomTaskResponse)
async def update_room_task(
    room_id: int,
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    allowed = await has_room_access(db, room_id, current_user)
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(RoomTask).where(RoomTask.id == task_id, RoomTask.room_id == room_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if "status" in payload:
        task.status = payload["status"]
        if task.status == "done":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None
            
    await db.commit()
    
    # Broadcast task update
    response_data = {
        "id": task.id,
        "description": task.description,
        "assignee_username": task.assignee_username,
        "status": task.status,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    }
    
    await manager.broadcast(
        room_id,
        {
            "type": "task_updated",
            "data": {
                **response_data,
                "created_at": response_data["created_at"].isoformat() if response_data["created_at"] else None,
                "completed_at": response_data["completed_at"].isoformat() if response_data["completed_at"] else None
            }
        }
    )
    
    return response_data
