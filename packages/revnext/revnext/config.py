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


@dataclass(frozen=True)
class RevNextConfig:
    """Configuration for Revolution Next (*.revolutionnext.com.au) API / report downloads."""

    base_url: str
    username: str
    password: str
    session_path: Optional[Path] = None

    @classmethod
    def from_env(
        cls,
        *,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_path: Optional[Path] = None,
        load_dotenv: bool = True,
    ) -> "RevNextConfig":
        """Build config from environment variables. Override any field by passing it explicitly.

        Env: REVNEXT_URL (full base URL), REVNEXT_USERNAME, REVNEXT_PASSWORD,
        optional REVNEXT_SESSION_PATH.
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
