from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TokenDecodeError(Exception):
    pass


def create_access_token(data: dict):
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)

    expire = issued_at + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire,
            "iat": issued_at,
            "token_type": "access"
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,
                "require_iat": True
            }
        )
    except JWTError as exc:
        raise TokenDecodeError(
            "Invalid or expired token"
        ) from exc

    if payload.get("token_type") != "access":
        raise TokenDecodeError(
            "Invalid token type"
        )

    if not isinstance(payload.get("sub"), str):
        raise TokenDecodeError(
            "Missing token subject"
        )

    return payload
