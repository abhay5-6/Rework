from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


def _get_csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)

    return [
        value.strip()
        for value in raw_value.split(",")
        if value.strip()
    ]


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        return int(raw_value)

    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer"
        ) from exc


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    jwt_secret: str
    algorithm: str
    access_token_expire_minutes: int
    frontend_url: str
    backend_url: str
    backend_cors_origins: list[str]
    websocket_allowed_origins: list[str]

    gemini_api_key: str | None
    gemini_model: str
    gemini_embedding_model: str

    websocket_message_rate_limit: int
    websocket_rate_limit_window_seconds: int
    websocket_max_message_length: int

    login_rate_limit: str
    register_rate_limit: str
    message_rate_limit: str
    ai_rate_limit: str

    memory_min_importance_score: int
    memory_min_content_length: int
    memory_max_content_length: int

    embedding_dimension: int
    password_reset_token_expire_hours: int
    email_verification_enabled: bool
    smtp_server: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None

    google_oauth_client_id: str | None
    google_oauth_client_secret: str | None
    github_oauth_client_id: str | None
    github_oauth_client_secret: str | None
    oauth_state_expire_minutes: int

    redis_url: str
    max_file_size_bytes: int
    workspace_storage_quota_bytes: int
    disallowed_file_extensions: set[str]
    allowed_file_mime_types: set[str]

    cookie_secure: bool
    cookie_samesite: str
    cookie_domain: str | None

    ai_enabled: bool
    ai_test_mode: bool
    ai_timeout_seconds: int




def load_settings() -> Settings:

    jwt_secret = (
        os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY")
    )

    if not jwt_secret:
        raise RuntimeError(
            "Missing required environment variable: JWT_SECRET"
        )

    frontend_url = _get_required_env(
        "FRONTEND_URL"
    )

    cors_origins = _get_csv_env(
        "BACKEND_CORS_ORIGINS",
        frontend_url
    )

    websocket_origins = _get_csv_env(
        "WEBSOCKET_ALLOWED_ORIGINS",
        ",".join(cors_origins)
    )

    if "*" in cors_origins:
        raise RuntimeError(
            "BACKEND_CORS_ORIGINS cannot include '*'"
        )

    if "*" in websocket_origins:
        raise RuntimeError(
            "WEBSOCKET_ALLOWED_ORIGINS cannot include '*'"
        )

    return Settings(

        app_env=os.getenv(
            "APP_ENV",
            "development"
        ),

        database_url=_get_required_env(
            "DATABASE_URL"
        ),

        jwt_secret=jwt_secret,

        algorithm=os.getenv(
            "ALGORITHM",
            "HS256"
        ),

        access_token_expire_minutes=_get_int_env(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            60
        ),

        frontend_url=frontend_url,

        backend_url=os.getenv(
            "BACKEND_URL",
            "http://localhost:8000"
        ).rstrip("/"),

        backend_cors_origins=cors_origins,

        websocket_allowed_origins=websocket_origins,

        gemini_api_key=os.getenv(
            "GEMINI_API_KEY"
        ),

        gemini_model=os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        ),

        gemini_embedding_model=os.getenv(
            "GEMINI_EMBEDDING_MODEL",
            "text-embedding-004"
        ),

        websocket_message_rate_limit=_get_int_env(
            "WEBSOCKET_MESSAGE_RATE_LIMIT",
            200
        ),

        websocket_rate_limit_window_seconds=_get_int_env(
            "WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS",
            10
        ),

        websocket_max_message_length=_get_int_env(
            "WEBSOCKET_MAX_MESSAGE_LENGTH",
            50000
        ),

        login_rate_limit=os.getenv(
            "LOGIN_RATE_LIMIT",
            "5/minute"
        ),

        register_rate_limit=os.getenv(
            "REGISTER_RATE_LIMIT",
            "3/minute"
        ),

        message_rate_limit=os.getenv(
            "MESSAGE_RATE_LIMIT",
            "30/minute"
        ),

        ai_rate_limit=os.getenv(
            "AI_RATE_LIMIT",
            "10/minute"
        ),

        memory_min_importance_score=_get_int_env(
            "MEMORY_MIN_IMPORTANCE_SCORE",
            3
        ),

        memory_min_content_length=_get_int_env(
            "MEMORY_MIN_CONTENT_LENGTH",
            24
        ),

        memory_max_content_length=_get_int_env(
            "MEMORY_MAX_CONTENT_LENGTH",
            4000
        ),

        embedding_dimension=_get_int_env(
            "EMBEDDING_DIMENSION",
            384
        ),

        password_reset_token_expire_hours=_get_int_env(
            "PASSWORD_RESET_TOKEN_EXPIRE_HOURS",
            24
        ),

        email_verification_enabled=os.getenv(
            "EMAIL_VERIFICATION_ENABLED",
            "false"
        ).lower() == "true",

        smtp_server=os.getenv(
            "SMTP_SERVER"
        ),

        smtp_port=_get_int_env(
            "SMTP_PORT",
            587
        ),

        smtp_user=os.getenv(
            "SMTP_USER"
        ),

        smtp_password=os.getenv(
            "SMTP_PASSWORD"
        ),

        google_oauth_client_id=os.getenv(
            "GOOGLE_OAUTH_CLIENT_ID"
        ),

        google_oauth_client_secret=os.getenv(
            "GOOGLE_OAUTH_CLIENT_SECRET"
        ),

        github_oauth_client_id=os.getenv(
            "GITHUB_OAUTH_CLIENT_ID"
        ),

        github_oauth_client_secret=os.getenv(
            "GITHUB_OAUTH_CLIENT_SECRET"
        ),

        oauth_state_expire_minutes=_get_int_env(
            "OAUTH_STATE_EXPIRE_MINUTES",
            10
        ),
        
        redis_url=os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        ),

        max_file_size_bytes=_get_int_env(
            "MAX_FILE_SIZE_BYTES",
            26214400
        ),

        workspace_storage_quota_bytes=_get_int_env(
            "WORKSPACE_STORAGE_QUOTA_BYTES",
            524288000
        ),

        disallowed_file_extensions=set(
            ext.strip().lower()
            for ext in os.getenv(
                "DISALLOWED_FILE_EXTENSIONS",
                ".exe,.bat,.cmd,.sh,.php,.py,.pl,.cgi,.html,.htm,.js,.svg"
            ).split(",")
            if ext.strip()
        ),

        allowed_file_mime_types=set(
            mime.strip().lower()
            for mime in os.getenv(
                "ALLOWED_FILE_MIME_TYPES",
                "text/plain,text/csv,application/pdf,image/jpeg,image/png,image/gif,image/webp"
            ).split(",")
            if mime.strip()
        ),

        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "yes"),
        cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax").lower(),
        cookie_domain=os.getenv("COOKIE_DOMAIN", None),

        ai_enabled=os.getenv("AI_ENABLED", "true").lower() in ("true", "1", "yes"),
        ai_test_mode=os.getenv("AI_TEST_MODE", "false").lower() in ("true", "1", "yes"),
        ai_timeout_seconds=_get_int_env("AI_TIMEOUT_SECONDS", 10)
    )




settings = load_settings()

DATABASE_URL = settings.database_url
APP_ENV = settings.app_env

SECRET_KEY = settings.jwt_secret
JWT_SECRET = settings.jwt_secret

ALGORITHM = settings.algorithm

ACCESS_TOKEN_EXPIRE_MINUTES = (
    settings.access_token_expire_minutes
)

FRONTEND_URL = settings.frontend_url

BACKEND_CORS_ORIGINS = (
    settings.backend_cors_origins
)

WEBSOCKET_ALLOWED_ORIGINS = (
    settings.websocket_allowed_origins
)

GEMINI_API_KEY = (
    settings.gemini_api_key
)

GEMINI_MODEL = (
    settings.gemini_model
)

GEMINI_EMBEDDING_MODEL = (
    settings.gemini_embedding_model
)

LOGIN_RATE_LIMIT = (
    settings.login_rate_limit
)

REGISTER_RATE_LIMIT = (
    settings.register_rate_limit
)

MESSAGE_RATE_LIMIT = (
    settings.message_rate_limit
)

AI_RATE_LIMIT = (
    settings.ai_rate_limit
)

WEBSOCKET_MESSAGE_RATE_LIMIT = (
    settings.websocket_message_rate_limit
)

WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS = (
    settings.websocket_rate_limit_window_seconds
)

WEBSOCKET_MAX_MESSAGE_LENGTH = (
    settings.websocket_max_message_length
)

MEMORY_MIN_IMPORTANCE_SCORE = (
    settings.memory_min_importance_score
)

MEMORY_MIN_CONTENT_LENGTH = (
    settings.memory_min_content_length
)

MEMORY_MAX_CONTENT_LENGTH = (
    settings.memory_max_content_length
)

MAX_FILE_SIZE_BYTES = settings.max_file_size_bytes
WORKSPACE_STORAGE_QUOTA_BYTES = settings.workspace_storage_quota_bytes
DISALLOWED_FILE_EXTENSIONS = settings.disallowed_file_extensions

ALLOWED_FILE_MIME_TYPES = settings.allowed_file_mime_types
