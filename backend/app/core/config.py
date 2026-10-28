import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _sqlalchemy_url(raw: str) -> str:
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql+psycopg://"):
        raw = "postgresql://" + raw[len("postgresql+psycopg://") :]
    if raw.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw[len("postgresql://") :]
    return raw


@dataclass(frozen=True)
class Settings:
    database_url: str
    auth_github_id: str
    auth_github_secret: str
    auth_secret: str
    backend_url: str
    frontend_url: str | None
    session_cookie_name: str = "session"
    state_cookie_name: str = "oauth_state"
    session_max_age: int = 60 * 60 * 24 * 7
    oauth_state_max_age: int = 60 * 10

    @property
    def sqlalchemy_url(self) -> str:
        return _sqlalchemy_url(self.database_url)

    @property
    def github_redirect_uri(self) -> str:
        return f"{self.backend_url}/auth/github/callback"

    @property
    def post_login_redirect(self) -> str:
        if self.frontend_url:
            return f"{self.frontend_url}/login"
        return f"{self.backend_url}/api/auth/me"

    @property
    def cookie_secure(self) -> bool:
        return self.backend_url.startswith("https://")


def _load_settings() -> Settings:
    backend_url = (
        os.getenv("BACKEND_URL") or os.getenv("AUTH_URL") or "http://localhost:8000"
    ).rstrip("/")
    frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/") or None
    return Settings(
        database_url=_required("DATABASE_URL"),
        auth_github_id=_required("AUTH_GITHUB_ID"),
        auth_github_secret=_required("AUTH_GITHUB_SECRET"),
        auth_secret=_required("AUTH_SECRET"),
        backend_url=backend_url,
        frontend_url=frontend_url,
    )


settings = _load_settings()
