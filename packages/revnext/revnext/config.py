"""
Configuration for Revolution Next (*.revolutionnext.com.au) report downloads.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _default_session_path() -> Path:
    """Default path for persisted session cookies (under cwd)."""
    return Path.cwd() / ".revnext-session.json"


DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 120.0
DEFAULT_TIMEOUT: tuple[float, float] = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)


def parse_timeout(value: str | None) -> tuple[float, float] | None:
    """Parse a timeout spec: "30" (read only) or "10,120" ((connect, read)).

    Returns None for empty or unparseable input so the caller keeps its default
    rather than accidentally running with no timeout at all.
    """
    if not value or not value.strip():
        return None
    parts = [p.strip() for p in value.split(",")]
    try:
        numbers = [float(p) for p in parts if p]
    except ValueError:
        return None
    if len(numbers) == 1:
        return (DEFAULT_CONNECT_TIMEOUT, numbers[0])
    if len(numbers) == 2:
        return (numbers[0], numbers[1])
    return None


def timeout_from_env() -> float | tuple[float, float]:
    """Request timeout from REVNEXT_TIMEOUT, else DEFAULT_TIMEOUT."""
    _load_dotenv_if_available()
    return parse_timeout(os.getenv("REVNEXT_TIMEOUT")) or DEFAULT_TIMEOUT


@dataclass(frozen=True)
class RevNextConfig:
    """Configuration for Revolution Next (*.revolutionnext.com.au) API / report downloads."""

    base_url: str
    username: str
    password: str
    session_path: Optional[Path] = None
    timeout: float | tuple[float, float] = DEFAULT_TIMEOUT

    @classmethod
    def from_env(
        cls,
        *,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_path: Optional[Path] = None,
        timeout: float | tuple[float, float] | None = None,
        load_dotenv: bool = True,
    ) -> "RevNextConfig":
        """Build config from environment variables. Override any field by passing it explicitly.

        Env: REVNEXT_URL (full base URL), REVNEXT_USERNAME, REVNEXT_PASSWORD,
        optional REVNEXT_SESSION_PATH, optional REVNEXT_TIMEOUT ("30" or "10,120").
        """
        if load_dotenv:
            _load_dotenv_if_available()
        url = (
            base_url
            or os.getenv("REVNEXT_URL")
            or "https://mikecarney.revolutionnext.com.au"
        )
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        uname = username or os.getenv("REVNEXT_USERNAME") or ""
        pwd = password or os.getenv("REVNEXT_PASSWORD") or ""
        sp = session_path
        if sp is None and os.getenv("REVNEXT_SESSION_PATH"):
            sp = Path(os.getenv("REVNEXT_SESSION_PATH"))
        if sp is None:
            sp = _default_session_path()
        return cls(
            base_url=url,
            username=uname,
            password=pwd,
            session_path=sp,
            timeout=timeout if timeout is not None else timeout_from_env(),
        )

    def validate(self) -> None:
        """Raise ValueError if required fields are missing."""
        if not self.username or not self.password:
            raise ValueError(
                "REVNEXT_USERNAME and REVNEXT_PASSWORD must be set "
                "(via RevNextConfig.from_env(), environment variables, or constructor)."
            )


def get_revnext_base_url_from_env() -> str:
    """Return RevNext base URL from environment (REVNEXT_URL)."""
    _load_dotenv_if_available()
    url = os.getenv("REVNEXT_URL") or "https://mikecarney.revolutionnext.com.au"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
