from sqlalchemy import String, DateTime, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from app.db.database import Base


class AuditLog(Base):
    """Track all important user actions for security and auditing"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_workspace_id", "workspace_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_user_action", "user_id", "action"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    workspace_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    resource_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True
    )

    # Common audit actions
    ACTIONS = {
        # Auth
        "LOGIN": "user_login",
        "REGISTER": "user_register",
        "LOGOUT": "user_logout",
        "PASSWORD_RESET_REQUEST": "password_reset_request",
        "PASSWORD_RESET": "password_reset",
        "EMAIL_VERIFY": "email_verify",
        "EMAIL_VERIFY_REQUEST": "email_verify_request",
        
        # Workspace management
        "CREATE_WORKSPACE": "create_workspace",
        "DELETE_WORKSPACE": "delete_workspace",
        "UPDATE_WORKSPACE": "update_workspace",
        
        # Member management
        "JOIN_WORKSPACE": "join_workspace",
        "LEAVE_WORKSPACE": "leave_workspace",
        "PROMOTE_MEMBER": "promote_member",
        "DEMOTE_MEMBER": "demote_member",
        "REMOVE_MEMBER": "remove_member",
        
        # Messages
        "SEND_MESSAGE": "send_message",
        "DELETE_MESSAGE": "delete_message",
        
        # Collaborators
        "REQUEST_COLLABORATION": "request_collaboration",
        "ACCEPT_COLLABORATION": "accept_collaboration",
        "REJECT_COLLABORATION": "reject_collaboration",
        
        # Security events
        "FAILED_LOGIN": "failed_login",
        "SUSPICIOUS_ACTIVITY": "suspicious_activity",
        "RATE_LIMIT_EXCEEDED": "rate_limit_exceeded",
        "UNAUTHORIZED_ACCESS": "unauthorized_access",
    }
