import hashlib
import hmac
import secrets

from starlette.responses import Response

from app.core.config import settings


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hmac.new(
        settings.auth_secret.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


def tokens_match(left: str, right: str) -> bool:
    if len(left) != len(right):
        return False
    return secrets.compare_digest(left, right)


def _cookie_kwargs(max_age: int) -> dict:
    return {
        "max_age": max_age,
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }


def set_state_cookie(response: Response, state: str) -> None:
    response.set_cookie(
        settings.state_cookie_name,
        state,
        **_cookie_kwargs(settings.oauth_state_max_age),
    )


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        **_cookie_kwargs(settings.session_max_age),
    )


def clear_cookie(response: Response, name: str) -> None:
    response.delete_cookie(
        name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
