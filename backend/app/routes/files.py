from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
import uuid
from typing import Dict, Any

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.room_service import get_room_by_id
from app.schemas.common import FileUploadResponse

router = APIRouter(prefix="/rooms", tags=["Files"])

UPLOAD_DIR = "uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/{room_id}/files", response_model=FileUploadResponse)
async def upload_file(
    room_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # 1. Check room access
    room = await get_room_by_id(db, room_id, current_user)
    if not room or not room.get("is_member"):
        if not room or room.get("is_private"):
            raise HTTPException(status_code=403, detail="Not authorized to upload files to this room")

    # 2. Setup directory
    room_upload_dir = os.path.join(UPLOAD_DIR, str(room_id))
    os.makedirs(room_upload_dir, exist_ok=True)

    # 3. Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(room_upload_dir, unique_filename)

    # 4. Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file")

    # 5. Return accessible URL
    file_url = f"/uploads/{room_id}/{unique_filename}"
    
    return {
        "file_url": file_url,
        "file_name": file.filename,
        "file_type": file.content_type
    }
