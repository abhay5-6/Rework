from datetime import datetime, timedelta, timezone
import re
import secrets
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.user import User
from app.models.user_identity import UserIdentity
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import AuthProvidersResponse
from app.core.exceptions import UserAlreadyExistsException
from app.services.user_service import authenticate_user, create_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.register_rate_limit)
async def register(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        created_user = await create_user(db, user)
        return created_user
    except UserAlreadyExistsException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/providers", response_model=AuthProvidersResponse)
async def get_providers():
    return {
        "google": bool(
            settings.google_oauth_client_id
            and settings.google_oauth_client_secret
        ),
        "github": bool(
            settings.github_oauth_client_id
            and settings.github_oauth_client_secret
        ),
    }


def _provider_config(provider: str) -> dict[str, str]:
    if provider == "google":
        client_id = settings.google_oauth_client_id
        client_secret = settings.google_oauth_client_secret
        return {
            "client_id": client_id or "",
            "client_secret": client_secret or "",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scope": "openid email profile",
        }

    if provider == "github":
        client_id = settings.github_oauth_client_id
        client_secret = settings.github_oauth_client_secret
        return {
            "client_id": client_id or "",
            "client_secret": client_secret or "",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scope": "read:user user:email",
        }

    raise HTTPException(status_code=404, detail="Unsupported OAuth provider")


def _redirect_uri(provider: str) -> str:
    return f"{settings.backend_url}/auth/{provider}/callback"


def _oauth_error(message: str) -> RedirectResponse:
    location = (
        f"{settings.frontend_url}/login?oauth_error={quote(message)}"
    )
    return RedirectResponse(location=location, status_code=302)


@router.get("/{provider}/start", response_model=None)
async def start_oauth(provider: str):
    config = _provider_config(provider)

    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(
            status_code=503,
            detail=f"{provider.title()} OAuth is not configured"
        )

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.oauth_state_expire_minutes
    )
    state = jwt.encode(
        {
            "provider": provider,
            "nonce": secrets.token_urlsafe(24),
            "exp": expires,
        },
        settings.jwt_secret,
        algorithm=settings.algorithm,
    )
    params = {
        "client_id": config["client_id"],
        "redirect_uri": _redirect_uri(provider),
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }

    return RedirectResponse(
        location=f"{config['authorize_url']}?{urlencode(params)}",
        status_code=302,
    )


async def _fetch_provider_profile(
    provider: str,
    code: str,
    config: dict[str, str]
) -> dict[str, str | bool]:
    async with httpx.AsyncClient(timeout=12) as client:
        token_response = await client.post(
            config["token_url"],
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": code,
                "redirect_uri": _redirect_uri(provider),
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError("Provider did not return an access token")

        if provider == "google":
            profile_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            return {
                "provider_user_id": str(profile["sub"]),
                "email": str(profile["email"]).lower(),
                "email_verified": bool(profile.get("email_verified")),
                "display_name": str(profile.get("name") or profile["email"]),
            }

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
        }
        profile_response = await client.get(
            "https://api.github.com/user",
            headers=headers,
        )
        profile_response.raise_for_status()
        profile = profile_response.json()

        emails_response = await client.get(
            "https://api.github.com/user/emails",
            headers=headers,
        )
        emails_response.raise_for_status()
        emails = emails_response.json()
        verified_email = next(
            (
                item["email"]
                for item in emails
                if item.get("verified") and item.get("primary")
            ),
            next(
                (item["email"] for item in emails if item.get("verified")),
                None,
            ),
        )

        if not verified_email:
            raise ValueError("GitHub did not return a verified email")

        return {
            "provider_user_id": str(profile["id"]),
            "email": str(verified_email).lower(),
            "email_verified": True,
            "display_name": str(profile.get("name") or profile["login"]),
        }


async def _unique_username(
    db: AsyncSession,
    display_name: str,
    email: str
) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]+", "", display_name).lower()
    base = (base or email.split("@", 1)[0] or "member")[:42]
    candidate = base
    suffix = 1

    while True:
        result = await db.execute(select(User).where(User.username == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base[:38]}_{suffix}"
        suffix += 1


@router.get("/{provider}/callback", response_model=None)
async def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if error or not code or not state:
        return _oauth_error("OAuth sign-in was cancelled")

    try:
        state_data = jwt.decode(
            state,
            settings.jwt_secret,
            algorithms=[settings.algorithm],
        )
        if state_data.get("provider") != provider:
            raise ValueError("OAuth provider mismatch")

        config = _provider_config(provider)
        profile = await _fetch_provider_profile(provider, code, config)
        if not profile["email_verified"]:
            raise ValueError("Provider email is not verified")

        identity_result = await db.execute(
            select(UserIdentity).where(
                UserIdentity.provider == provider,
                UserIdentity.provider_user_id == profile["provider_user_id"],
            )
        )
        identity = identity_result.scalar_one_or_none()

        if identity:
            user_result = await db.execute(
                select(User).where(User.id == identity.user_id)
            )
            user = user_result.scalar_one()
        else:
            user_result = await db.execute(
                select(User).where(User.email == profile["email"])
            )
            user = user_result.scalar_one_or_none()

            if not user:
                user = User(
                    username=await _unique_username(
                        db,
                        str(profile["display_name"]),
                        str(profile["email"]),
                    ),
                    email=str(profile["email"]),
                    hashed_password=hash_password(secrets.token_urlsafe(32)),
                    email_verified=True,
                )
                db.add(user)
                await db.flush()
            else:
                user.email_verified = True

            db.add(UserIdentity(
                user_id=user.id,
                provider=provider,
                provider_user_id=str(profile["provider_user_id"]),
                provider_email=str(profile["email"]),
            ))
            await db.commit()

        token = create_access_token(data={"sub": user.email})
        return RedirectResponse(
            location=f"{settings.frontend_url}/auth/callback?token={quote(token)}",
            status_code=302,
        )
    except (JWTError, KeyError, ValueError, httpx.HTTPError) as exc:
        return _oauth_error(str(exc) if settings.app_env == "development" else "OAuth sign-in failed")
