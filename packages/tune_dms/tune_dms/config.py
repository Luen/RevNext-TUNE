"""
Configuration for TUNE DMS (desktop GUI automation).
Users can set settings via environment variables or pass config programmatically.
"""

import os
from dataclasses import dataclass
from typing import Optional


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@dataclass(frozen=True)
class TuneConfig:
    """Configuration for TUNE DMS (desktop GUI automation)."""

    user_id: str
    password: str
    shortcut_path: str = r"C:\Users\Public\Desktop\TUNE.lnk"
    images_dir: Optional[str] = None
    reports_dir: Optional[str] = None

    @classmethod
    def from_env(
        cls,
        *,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        shortcut_path: Optional[str] = None,
        images_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
        load_dotenv: bool = True,
    ) -> "TuneConfig":
        """Build config from environment variables. Override any field by passing it explicitly."""
        if load_dotenv:
            _load_dotenv_if_available()
        return cls(
            user_id=user_id or os.getenv("TUNE_USER_ID") or "",
            password=password or os.getenv("TUNE_USER_PASSWORD") or "",
            shortcut_path=shortcut_path or os.getenv("TUNE_SHORTCUT_PATH") or cls.shortcut_path,
            images_dir=images_dir or os.getenv("TUNE_IMAGES_DIR"),
            reports_dir=reports_dir or os.getenv("TUNE_REPORTS_DIR"),
        )

    def validate(self) -> None:
        """Raise ValueError if required fields are missing."""
        if not self.user_id or not self.password:
            raise ValueError(
                "TUNE_USER_ID and TUNE_USER_PASSWORD must be set "
                "(via TuneConfig.from_env(), environment variables, or constructor)."
            )
