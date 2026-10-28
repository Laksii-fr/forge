from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.core.security import (
    clear_cookie,
    new_token,
    set_session_cookie,
    set_state_cookie,
    tokens_match,
)
from app.db.models import User
from app.schemas.user import UserOut
from app.services.auth import revoke_session, start_session
from app.services.github import GitHubAuthError, fetch_github_profile

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


def login_failure(message: str) -> RedirectResponse:
    if not settings.frontend_url:
        raise BadRequestError(message)

    response = RedirectResponse(
        f"{settings.frontend_url}/login?{urlencode({'error': message})}",
        status_code=302,
    )
    response.headers["Cache-Control"] = "no-store"
    clear_cookie(response, settings.state_cookie_name)
    return response


@router.get("/github")
async def github_login() -> RedirectResponse:
    state = new_token()
    query = urlencode(
        {
            "client_id": settings.auth_github_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
    )
    response = RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{query}", status_code=302)
    response.headers["Cache-Control"] = "no-store"
    set_state_cookie(response, state)
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    if error:
        return login_failure(error_description or error)

    saved_state = request.cookies.get(settings.state_cookie_name)
    if not code or not state or not saved_state or not tokens_match(state, saved_state):
        return login_failure("Invalid OAuth state")

    try:
        profile = await fetch_github_profile(code)
    except GitHubAuthError as exc:
        return login_failure(str(exc))

    raw_token = await start_session(db, profile)
    response = RedirectResponse(settings.post_login_redirect, status_code=302)
    response.headers["Cache-Control"] = "no-store"
    set_session_cookie(response, raw_token)
    clear_cookie(response, settings.state_cookie_name)
    return response


@router.get("/me", response_model=UserOut)
async def me(response: Response, user: User = Depends(get_current_user)) -> User:
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        await revoke_session(db, raw_token)
    response = JSONResponse({"status": "logged_out"})
    response.headers["Cache-Control"] = "no-store"
    clear_cookie(response, settings.session_cookie_name)
    clear_cookie(response, settings.state_cookie_name)
    return response
