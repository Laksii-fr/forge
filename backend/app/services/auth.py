from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.security import hash_token, new_token
from app.db.models import AuthSession, User, utcnow
from app.services.github import GitHubProfile


async def start_session(db: AsyncSession, profile: GitHubProfile) -> str:
    user = await db.scalar(select(User).where(User.github_id == profile.github_id))

    if user is None:
        user = User(
            github_id=profile.github_id,
            login=profile.login,
            name=profile.name,
            email=profile.email,
            avatar_url=profile.avatar_url,
        )
        db.add(user)
        await db.flush()
    else:
        user.login = profile.login
        user.name = profile.name
        user.email = profile.email
        user.avatar_url = profile.avatar_url
        user.updated_at = utcnow()

    raw_token = new_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=utcnow() + timedelta(seconds=settings.session_max_age),
        )
    )
    await db.commit()
    return raw_token


async def get_user_by_session(db: AsyncSession, raw_token: str):
    auth_session = await db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.user))
        .where(AuthSession.token_hash == hash_token(raw_token))
    )
    if auth_session is None:
        return None

    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utcnow().tzinfo)
    if expires_at <= utcnow():
        await db.delete(auth_session)
        await db.commit()
        return None

    return auth_session.user


async def revoke_session(db: AsyncSession, raw_token: str) -> None:
    await db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    await db.commit()
