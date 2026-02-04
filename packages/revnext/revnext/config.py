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


@dataclass(frozen=True)
class RevNextConfig:
    """Configuration for Revolution Next (*.revolutionnext.com.au) API / report downloads."""

    base_url: str
    cookies_path: Optional[Path] = None
    username: Optional[str] = None
    password: Optional[str] = None

    @classmethod
    def from_env(
        cls,
        *,
        base_url: Optional[str] = None,
        cookies_path: Optional[Path] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        load_dotenv: bool = True,
    ) -> "RevNextConfig":
        """Build config from environment variables. Override any field by passing it explicitly."""
        if load_dotenv:
            _load_dotenv_if_available()
        url = base_url or os.getenv("REVOLUTIONNEXT_URL") or "https://mikecarney.revolutionnext.com.au"
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        cp = cookies_path
        if cp is None and os.getenv("REVOLUTIONNEXT_COOKIES_PATH"):
            cp = Path(os.getenv("REVOLUTIONNEXT_COOKIES_PATH"))
        return cls(
            base_url=url,
            cookies_path=cp,
            username=username or os.getenv("REVOLUTIONNEXT_USERNAME"),
            password=password or os.getenv("REVOLUTIONNEXT_PASSWORD"),
        )


def get_revnext_base_url_from_env() -> str:
    """Return RevNext base URL from environment (REVOLUTIONNEXT_URL)."""
    _load_dotenv_if_available()
    url = os.getenv("REVOLUTIONNEXT_URL") or "https://mikecarney.revolutionnext.com.au"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
