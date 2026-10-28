from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.exceptions import AppError

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class GitHubAuthError(AppError):
    status_code = 401
    detail = "GitHub authentication failed"


@dataclass(frozen=True)
class GitHubProfile:
    github_id: int
    login: str
    name: str | None
    email: str | None
    avatar_url: str | None


async def fetch_github_profile(code: str) -> GitHubProfile:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            access_token = await _exchange_code(client, code)
            return await _load_profile(client, access_token)
    except httpx.HTTPError as exc:
        raise GitHubAuthError("GitHub request failed") from exc


async def _exchange_code(client: httpx.AsyncClient, code: str) -> str:
    response = await client.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.auth_github_id,
            "client_secret": settings.auth_github_secret,
            "code": code,
            "redirect_uri": settings.github_redirect_uri,
        },
        headers={"Accept": "application/json"},
    )
    if response.status_code != 200:
        raise GitHubAuthError("GitHub token exchange failed")

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        description = payload.get("error_description") or payload.get("error")
        raise GitHubAuthError(description or "GitHub token exchange failed")
    return token


async def _load_profile(client: httpx.AsyncClient, access_token: str) -> GitHubProfile:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "forge-backend",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    user_response = await client.get(GITHUB_USER_URL, headers=headers)
    if user_response.status_code != 200:
        raise GitHubAuthError("GitHub user lookup failed")
    user = user_response.json()

    email = user.get("email")
    if not email:
        email_response = await client.get(GITHUB_EMAILS_URL, headers=headers)
        if email_response.status_code == 200:
            email = _primary_email(email_response.json())

    github_id = user.get("id")
    login = user.get("login")
    if not isinstance(github_id, int) or not isinstance(login, str) or not login:
        raise GitHubAuthError("GitHub profile was incomplete")

    name = user.get("name")
    avatar_url = user.get("avatar_url")
    return GitHubProfile(
        github_id=github_id,
        login=login,
        name=name if isinstance(name, str) else None,
        email=email if isinstance(email, str) else None,
        avatar_url=avatar_url if isinstance(avatar_url, str) else None,
    )


def _primary_email(emails: object) -> str | None:
    if not isinstance(emails, list):
        return None
    verified = [
        item
        for item in emails
        if isinstance(item, dict) and item.get("verified") and isinstance(item.get("email"), str)
    ]
    for item in verified:
        if item.get("primary"):
            return item["email"]
    if verified:
        return verified[0]["email"]
    return None
