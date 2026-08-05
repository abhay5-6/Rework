import os
import shutil
import uuid
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, get_current_user_from_header_or_param
from app.models.user import User
from app.services.workspace_service import get_workspace_by_id
from app.schemas.common import FileUploadResponse
from app.core.config import (
    MAX_FILE_SIZE_BYTES,
    WORKSPACE_STORAGE_QUOTA_BYTES,
    DISALLOWED_FILE_EXTENSIONS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["Files"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_workspace_storage_usage(workspace_id: int) -> int:
    """
    Calculates total byte size of files stored in a workspace's upload directory.
    
    Args:
        workspace_id: The ID of the workspace.
        
    Returns:
        Total bytes consumed by workspace files.
    """
    workspace_upload_dir = os.path.join(UPLOAD_DIR, str(workspace_id))
    if not os.path.exists(workspace_upload_dir):
        return 0

    total_bytes = 0
    with os.scandir(workspace_upload_dir) as entries:
        for entry in entries:
            if entry.is_file(follow_symlinks=False):
                total_bytes += entry.stat().st_size
    return total_bytes


@router.post("/{workspace_id}/files", response_model=FileUploadResponse)
async def upload_file(
    workspace_id: int = Path(..., description="Target workspace ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Uploads a file to a workspace.
    Requires active workspace membership for both public and private workspaces.
    Enforces maximum file size limits, disallowed extension blacklists, and workspace storage quotas.
    
    Args:
        workspace_id: The target workspace ID.
        file: The uploaded multipart file.
        db: Database session dependency.
        current_user: The authenticated user uploading the file.
        
    Returns:
        Dict containing file_url, file_name, and file_type.
        
    Raises:
        HTTPException 403: If user is not a member of the workspace.
        HTTPException 400: If file extension is disallowed or storage quota is exceeded.
        HTTPException 413: If file size exceeds maximum permitted limit.
        HTTPException 500: If saving the file to storage fails.
    """
    # 1. Check workspace membership (required for all workspaces)
    workspace = await get_workspace_by_id(db, workspace_id, current_user)
    if not workspace or not workspace.get("is_member"):
        logger.warning(
            "Upload rejected: User is not a member of workspace",
            extra={"workspace_id": workspace_id, "user_id": current_user.id}
        )
        raise HTTPException(
            status_code=403,
            detail="Not authorized to upload files to this workspace"
        )

    filename = file.filename or "file"
    ext = os.path.splitext(filename)[1].lower()

    # 2. Check disallowed file extensions
    if ext in DISALLOWED_FILE_EXTENSIONS:
        logger.warning(
            "Upload rejected: Extension disallowed",
            extra={"workspace_id": workspace_id, "user_id": current_user.id, "extension": ext}
        )
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not allowed for security reasons"
        )

    # 3. Setup directory
    workspace_upload_dir = os.path.join(UPLOAD_DIR, str(workspace_id))
    os.makedirs(workspace_upload_dir, exist_ok=True)

    # 4. Save file while checking size limit
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(workspace_upload_dir, unique_filename)

    total_uploaded = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_uploaded += len(chunk)
                if total_uploaded > MAX_FILE_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    logger.warning(
                        "Upload rejected: File size exceeds limit",
                        extra={
                            "workspace_id": workspace_id,
                            "user_id": current_user.id,
                            "file_size": total_uploaded,
                            "max_limit": MAX_FILE_SIZE_BYTES
                        }
                    )
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(
            f"Failed to write file to disk: {e}",
            extra={"workspace_id": workspace_id, "user_id": current_user.id}
        )
        raise HTTPException(status_code=500, detail="Failed to upload file")

    # 5. Enforce workspace storage quota
    current_storage = _get_workspace_storage_usage(workspace_id)
    if current_storage > WORKSPACE_STORAGE_QUOTA_BYTES:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.warning(
            "Upload rejected: Workspace quota exceeded",
            extra={
                "workspace_id": workspace_id,
                "current_usage": current_storage,
                "quota": WORKSPACE_STORAGE_QUOTA_BYTES
            }
        )
        raise HTTPException(
            status_code=400,
            detail="Workspace storage quota exceeded"
        )

    # 6. Return accessible download URL
    file_url = f"/workspaces/{workspace_id}/files/{unique_filename}"
    
    logger.info(
        "File uploaded successfully",
        extra={
            "workspace_id": workspace_id,
            "user_id": current_user.id,
            "file_name": filename,
            "file_size": total_uploaded
        }
    )

    return {
        "file_url": file_url,
        "file_name": filename,
        "file_type": file.content_type
    }


@router.get("/{workspace_id}/files/{filename}")
async def download_file(
    workspace_id: int = Path(..., description="Target workspace ID"),
    filename: str = Path(..., description="Target filename"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_header_or_param)
) -> FileResponse:
    """
    Downloads or views a workspace file.
    Requires user authentication (via Authorization header or ?token= query parameter) and active workspace membership.
    Protects against path traversal attacks.
    
    Args:
        workspace_id: The target workspace ID.
        filename: The requested filename.
        db: Database session dependency.
        current_user: The authenticated user requesting the file.
        
    Returns:
        FileResponse containing the requested file.
        
    Raises:
        HTTPException 400: If filename contains path traversal syntax.
        HTTPException 403: If user is not a member of the workspace.
        HTTPException 404: If file does not exist.
    """
    # 1. Path traversal security check
    safe_filename = os.path.basename(filename)
    if safe_filename != filename or ".." in filename or "\x00" in filename:
        logger.warning(
            "Download rejected: Path traversal attempt detected",
            extra={"workspace_id": workspace_id, "user_id": current_user.id, "raw_filename": filename}
        )
        raise HTTPException(status_code=400, detail="Invalid filename format")

    # 2. Check workspace membership
    workspace = await get_workspace_by_id(db, workspace_id, current_user)
    if not workspace or not workspace.get("is_member"):
        logger.warning(
            "Download rejected: User is not a member of workspace",
            extra={"workspace_id": workspace_id, "user_id": current_user.id, "target_filename": filename}
        )

        raise HTTPException(
            status_code=403,
            detail="Not authorized to access files in this workspace"
        )

    # 3. Resolve file location
    workspace_upload_dir = os.path.abspath(os.path.join(UPLOAD_DIR, str(workspace_id)))
    file_path = os.path.abspath(os.path.join(workspace_upload_dir, safe_filename))

    if not file_path.startswith(workspace_upload_dir + os.sep) and file_path != workspace_upload_dir:
        logger.warning(
            "Download rejected: Path outside workspace upload directory",
            extra={"workspace_id": workspace_id, "user_id": current_user.id, "file_path": file_path}
        )
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        headers={"X-Content-Type-Options": "nosniff"}
    )
