from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotAuthenticatedError
from app.db.models import User
from app.db.session import SessionLocal
from app.services.auth import get_user_by_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    raw_token = request.cookies.get(settings.session_cookie_name)
    user = await get_user_by_session(db, raw_token) if raw_token else None
    if user is None:
        raise NotAuthenticatedError()
    return user
