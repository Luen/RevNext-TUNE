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


def _optional_int_env(name: str) -> Optional[int]:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return None
    try:
        return int(val.strip())
    except ValueError:
        return None


@dataclass(frozen=True)
class TuneConfig:
    """Configuration for TUNE DMS (desktop GUI automation)."""

    user_id: str
    password: str
    shortcut_path: str = r"C:\Users\Public\Desktop\TUNE.lnk"
    images_dir: Optional[str] = None
    reports_dir: Optional[str] = None
    # Optional reset indices when TUNE is already open (reset flow): select by index
    # (e.g. department_index=2 selects 3rd department). None = do nothing for that field.
    department_index: Optional[int] = None
    division_index: Optional[int] = None
    company_index: Optional[int] = None

    @classmethod
    def from_env(
        cls,
        *,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        shortcut_path: Optional[str] = None,
        images_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
        department_index: Optional[int] = None,
        division_index: Optional[int] = None,
        company_index: Optional[int] = None,
        load_dotenv: bool = True,
    ) -> "TuneConfig":
        """Build config from environment variables. Override any field by passing it explicitly."""
        if load_dotenv:
            _load_dotenv_if_available()
        return cls(
            user_id=user_id or os.getenv("TUNE_USER_ID") or "",
            password=password or os.getenv("TUNE_USER_PASSWORD") or "",
            shortcut_path=shortcut_path
            or os.getenv("TUNE_SHORTCUT_PATH")
            or cls.shortcut_path,
            images_dir=images_dir or os.getenv("TUNE_IMAGES_DIR"),
            reports_dir=reports_dir or os.getenv("TUNE_REPORTS_DIR"),
            department_index=department_index
            if department_index is not None
            else _optional_int_env("TUNE_RESET_DEPARTMENT_INDEX"),
            division_index=division_index
            if division_index is not None
            else _optional_int_env("TUNE_RESET_DIVISION_INDEX"),
            company_index=company_index
            if company_index is not None
            else _optional_int_env("TUNE_RESET_COMPANY_INDEX"),
        )

    def validate(self) -> None:
        """Raise ValueError if required fields are missing."""
        if not self.user_id or not self.password:
            raise ValueError(
                "TUNE_USER_ID and TUNE_USER_PASSWORD must be set "
                "(via TuneConfig.from_env(), environment variables, or constructor)."
            )
