"""Audit logging utilities for tracking user actions and security events"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


async def log_audit_event(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    room_id: int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
    status: str = "success"
) -> AuditLog | None:
    """
    Log an audit event to the database.

    Args:
        db: Database session
        user_id: ID of user performing action
        action: Action code (from AuditLog.ACTIONS)
        resource_type: Type of resource (e.g., 'room', 'message', 'user')
        resource_id: ID of the resource affected
        room_id: Room ID if applicable
        details: Additional details about the action
        ip_address: IP address of the request
        status: Success/failure status

    Returns:
        Created AuditLog instance or None if logging fails
    """
    try:
        audit = AuditLog(
            user_id=user_id,
            room_id=room_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            status=status
        )
        db.add(audit)
        await db.flush()
        return audit
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        return None


async def log_security_event(
    db: AsyncSession,
    action: str,
    user_id: int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
    status: str = "failure"
) -> AuditLog | None:
    """Log a security-related event"""
    return await log_audit_event(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="security",
        details=details,
        ip_address=ip_address,
        status=status
    )


async def log_auth_event(
    db: AsyncSession,
    action: str,
    user_id: int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
    status: str = "success"
) -> AuditLog | None:
    """Log authentication events (login, register, password reset, etc.)"""
    return await log_audit_event(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="auth",
        details=details,
        ip_address=ip_address,
        status=status
    )
