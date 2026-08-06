import os
import uuid
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.workspace_service import get_workspace_by_id
from app.schemas.common import FileUploadResponse
from app.core.config import (
    MAX_FILE_SIZE_BYTES,
    WORKSPACE_STORAGE_QUOTA_BYTES,
    DISALLOWED_FILE_EXTENSIONS,
    ALLOWED_FILE_MIME_TYPES
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["Files"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_FILE_TYPES = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


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


def _is_allowed_file_type(filename: str, content_type: str) -> bool:
    """
    Validates file type using both extension and MIME type.
    Uses allowlist approach for better security.

    Args:
        filename: Original filename
        content_type: Declared MIME type from upload

    Returns:
        True if file type is allowed, False otherwise
    """
    # Get extension
    ext = os.path.splitext(filename)[1].lower()

    # Check extension blocklist (defense in depth)
    if ext in DISALLOWED_FILE_EXTENSIONS:
        return False

    expected_content_type = ALLOWED_FILE_TYPES.get(ext)
    return (
        expected_content_type is not None
        and content_type == expected_content_type
        and content_type in ALLOWED_FILE_MIME_TYPES
    )


def _get_content_disposition(filename: str) -> str:
    """
    Generates proper Content-Disposition header value.

    Args:
        filename: Original filename

    Returns:
        Content-Disposition header value
    """
    # Sanitize filename for header
    safe_filename = "".join(c for c in filename if c.isprintable() and c not in '<>:"|?*')
    if not safe_filename:
        safe_filename = "download"

    # Always use attachment for security - browsers will handle preview appropriately
    # based on content-type and file extension
    return f'attachment; filename="{safe_filename}"'


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
    Enforces maximum file size limits, allowed MIME types, and workspace storage quotas.

    Args:
        workspace_id: The target workspace ID.
        file: The uploaded multipart file.
        db: Database session dependency.
        current_user: The authenticated user uploading the file.

    Returns:
        Dict containing file_url, file_name, and file_type.

    Raises:
        HTTPException 403: If user is not a member of the workspace.
        HTTPException 400: If file type is not allowed or storage quota is exceeded.
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
    content_type = file.content_type or "application/octet-stream"

    # 2. Validate file type using allowlist approach
    if not _is_allowed_file_type(filename, content_type):
        logger.warning(
            "Upload rejected: File type not allowed",
            extra={
                "workspace_id": workspace_id,
                "user_id": current_user.id,
                "filename": filename,
                "content_type": content_type
            }
        )
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' is not allowed for security reasons"
        )

    # 3. Setup directory
    workspace_upload_dir = os.path.join(UPLOAD_DIR, str(workspace_id))
    os.makedirs(workspace_upload_dir, exist_ok=True)

    # 4. Save file while checking size limit
    ext = os.path.splitext(filename)[1].lower()
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
        "file_type": content_type
    }


@router.get("/{workspace_id}/files/{filename}")
async def download_file(
    workspace_id: int = Path(..., description="Target workspace ID"),
    filename: str = Path(..., description="Target filename"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FileResponse:
    """
    Downloads or views a workspace file.
    Requires user authentication (via Authorization header) and active workspace membership.
    Protects against path traversal attacks.
    Serves files with appropriate security headers.

    Args:
        workspace_id: The target workspace ID.
        filename: The requested filename.
        db: Database session dependency.
        current_user: The authenticated user requesting the file.

    Returns:
        FileResponse containing the requested file with proper headers.

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
            extra={
                "workspace_id": workspace_id,
                "user_id": getattr(current_user, 'id', 'unknown'),
                "raw_filename": filename
            }
        )
        raise HTTPException(status_code=400, detail="Invalid filename format")

    # 2. Check workspace membership
    workspace = await get_workspace_by_id(db, workspace_id, current_user)
    if not workspace or not workspace.get("is_member"):
        logger.warning(
            "Download rejected: User is not a member of workspace",
            extra={
                "workspace_id": workspace_id,
                "user_id": getattr(current_user, 'id', 'unknown'),
                "target_filename": filename
            }
        )

        raise HTTPException(
            status_code=403,
            detail="Not authorized to access files in this workspace"
        )

    # 3. Resolve file location
    workspace_upload_dir = os.path.abspath(os.path.join(UPLOAD_DIR, str(workspace_id)))
    file_path = os.path.abspath(os.path.join(workspace_upload_dir, safe_filename))

    # Additional path traversal check after resolving path
    if not file_path.startswith(workspace_upload_dir + os.sep) and file_path != workspace_upload_dir:
        logger.warning(
            "Download rejected: Path outside workspace upload directory",
            extra={
                "workspace_id": workspace_id,
                "user_id": getattr(current_user, 'id', 'unknown'),
                "file_path": file_path
            }
        )
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    extension = os.path.splitext(safe_filename)[1].lower()
    content_type = ALLOWED_FILE_TYPES.get(
        extension,
        "application/octet-stream"
    )

    # Prepare headers
    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
        # Important: Use attachment to prevent automatic execution in browser
        "Content-Disposition": _get_content_disposition(safe_filename)
    }

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=content_type,
        headers=headers
    )
