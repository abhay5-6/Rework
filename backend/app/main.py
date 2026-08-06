from fastapi import (
    FastAPI,
    Request
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import engine
from app.routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException
from app.routes.workspaces import router as rooms_router
from app.routes.messages import router as messages_router
from app.websocket.chat import router as websocket_router
from contextlib import asynccontextmanager
from app.db.database import Base
from app.core.config import BACKEND_CORS_ORIGINS, settings
from app.core.exceptions import (
    database_exception_handler,
    http_exception_handler,
    rate_limit_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler
)
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter
from app.routes import collaborators, files
from app.models.workspace_memory import WorkspaceMemory
from app.models.workspace_task import WorkspaceTask
from app.routes.memories import router as memories_router
from app.routes.ai_summary import router as ai_summary_router
from app.routes.ai_graph import router as ai_graph_router
import logging
from uuid import uuid4


configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.websocket.redis_pubsub import redis_manager
    from app.websocket.manager import manager
    from arq import create_pool
    from app.worker import redis_settings
    import asyncio

    if settings.app_env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("development_mode: ran create_all")
        
    await redis_manager.connect()
    redis_manager._listener_task = asyncio.create_task(
        redis_manager.listen(manager.broadcast_local)
    )
    
    # Initialize ARQ queue pool
    try:
        app.state.arq_pool = await create_pool(redis_settings)
        logger.info("Successfully connected to ARQ Redis Pool")
    except Exception as e:
        logger.error(f"Failed to connect to ARQ Redis Pool: {e}. Background tasks will run synchronously.")
        app.state.arq_pool = None
    
    yield
    
    await redis_manager.disconnect()
    
    if hasattr(app.state, "arq_pool"):
        await app.state.arq_pool.close()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type"
    ],
)
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(
    HTTPException,
    http_exception_handler
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)
app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_exception_handler
)
app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler
)
app.add_exception_handler(
    Exception,
    unhandled_exception_handler
)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid4())
    )
    request.state.request_id = request_id

    logger.info(
        "request_started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path
        }
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    logger.info(
        "request_finished",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        }
    )

    return response
from app.routes.tasks import router as tasks_router
from app.routes.organization import router as org_router
from app.routes.channel import router as channel_router
from app.routes.admin import router as admin_router

app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(messages_router)
app.include_router(websocket_router)
app.include_router(collaborators.router)
app.include_router(memories_router)
app.include_router(ai_summary_router)
app.include_router(
    ai_graph_router,
)
app.include_router(files.router)
app.include_router(tasks_router)
app.include_router(org_router, prefix="/orgs", tags=["Organizations"])
app.include_router(channel_router, prefix="/channels", tags=["Channels"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/")
def root():
    return {"message": "Rework backend running"}


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.get("/db-test")
async def db_test():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar()
        }

    except Exception as e:
        return {
            "database": "failed",
            "error": str(e)
        }
