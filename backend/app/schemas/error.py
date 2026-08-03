"""Standardized API error response models"""

from pydantic import BaseModel
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for consistent API responses"""
    
    # Auth errors
    INVALID_CREDENTIALS = "invalid_credentials"
    EXPIRED_TOKEN = "expired_token"
    INVALID_TOKEN = "invalid_token"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    
    # User errors
    USER_NOT_FOUND = "user_not_found"
    USER_ALREADY_EXISTS = "user_already_exists"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    WEAK_PASSWORD = "weak_password"
    
    # Workspace errors
    WORKSPACE_NOT_FOUND = "workspace_not_found"
    WORKSPACE_ALREADY_EXISTS = "workspace_already_exists"
    NOT_WORKSPACE_MEMBER = "not_workspace_member"
    NOT_WORKSPACE_OWNER = "not_workspace_owner"
    
    # Validation errors
    INVALID_INPUT = "invalid_input"
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    
    # Business logic errors
    ALREADY_MEMBER = "already_member"
    CANNOT_REMOVE_OWNER = "cannot_remove_owner"
    OPERATION_FAILED = "operation_failed"
    
    # Rate limit errors
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Server errors
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ErrorDetail(BaseModel):
    """Standardized error detail model"""
    code: ErrorCode
    message: str
    details: dict[str, object] | None = None
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standardized API error response"""
    success: bool = False
    error: ErrorDetail
    request_id: str | None = None


class SuccessResponse(BaseModel):
    """Standardized API success response"""
    success: bool = True
    data: dict[str, object] | None = None
    message: str | None = None


def create_error_response(
    code: ErrorCode,
    message: str,
    details: dict[str, object] | None = None,
    field: str | None = None,
    request_id: str | None = None
) -> ErrorResponse:
    """Helper function to create standardized error responses"""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
            field=field
        ),
        request_id=request_id
    )


def create_success_response(
    data: dict[str, object] | None = None,
    message: str | None = None
) -> SuccessResponse:
    """Helper function to create standardized success responses"""
    return SuccessResponse(
        data=data,
        message=message
    )
