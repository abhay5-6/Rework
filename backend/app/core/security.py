import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TokenDecodeError(Exception):
    pass


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    
    Args:
        password: The plain text password.
        
    Returns:
        The hashed password string.
    """
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verifies a plain text password against a bcrypt hash.
    
    Args:
        plain_password: The plain text password to check.
        hashed_password: The stored bcrypt hash string.
        
    Returns:
        True if password matches, False otherwise.
    """
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """
    Encodes data payload into a JWT access token.
    
    Args:
        data: Dictionary payload containing user metadata (e.g. sub: email).
        
    Returns:
        Encoded JWT token string.
    """
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
    """
    Decodes and validates a JWT access token.
    
    Args:
        token: Encoded JWT token string.
        
    Returns:
        Decoded payload dictionary.
        
    Raises:
        TokenDecodeError: If token is invalid, expired, or missing claims.
    """
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
