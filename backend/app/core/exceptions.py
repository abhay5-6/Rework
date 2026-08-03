import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


logger = logging.getLogger(__name__)


class DomainException(Exception):
    """Base domain exception for service-layer business errors."""


class UserAlreadyExistsException(DomainException):
    """Raised when an account already exists for provided identity data."""


class EmailAlreadyRegisteredException(UserAlreadyExistsException):
    def __init__(self) -> None:
        super().__init__("Email already registered")


class UsernameAlreadyTakenException(UserAlreadyExistsException):
    def __init__(self) -> None:
        super().__init__("Username already taken")


class RoomAlreadyExistsException(DomainException):
    def __init__(self) -> None:
        super().__init__("Workspace already exists")


class RoomNotFoundException(DomainException):
    def __init__(self) -> None:
        super().__init__("Workspace not found")


class RoomAlreadyJoinedException(DomainException):
    def __init__(self) -> None:
        super().__init__("Already joined")


class RoomJoinRequestPendingException(DomainException):
    def __init__(self) -> None:
        super().__init__("Request already pending")


class WorkspaceMembershipRequiredException(DomainException):
    def __init__(self) -> None:
        super().__init__("Not a member")


class RoomOwnerCannotLeaveException(DomainException):
    def __init__(self) -> None:
        super().__init__("Owner cannot leave workspace")


class OrganizationMembershipRequiredException(DomainException):
    def __init__(self) -> None:
        super().__init__("Organization membership required")


class RoomOwnerRequiredException(DomainException):
    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message)


class JoinRequestNotFoundException(DomainException):
    def __init__(self) -> None:
        super().__init__("Request not found")


class AlreadyMemberException(DomainException):
    def __init__(self) -> None:
        super().__init__("Already member")


def _request_context(request: Request) -> dict:
    return {
        "path": request.url.path,
        "method": getattr(request, "method", "WEBSOCKET"),
        "request_id": getattr(
            request.state,
            "request_id",
            None
        )
    }


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    logger.warning(
        "http_exception",
        extra={
            **_request_context(request),
            "status_code": exc.status_code
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    logger.warning(
        "request_validation_error",
        extra=_request_context(request)
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


async def rate_limit_exception_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    logger.warning(
        "rate_limit_exceeded",
        extra=_request_context(request)
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "type": "rate_limit_exceeded",
                "message": "Rate limit exceeded"
            }
        }
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    logger.exception(
        "database_error",
        extra=_request_context(request)
    )

    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "type": "database_error",
                "message": "Database operation failed"
            }
        }
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        extra=_request_context(request)
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "Internal server error"
            }
        }
    )
