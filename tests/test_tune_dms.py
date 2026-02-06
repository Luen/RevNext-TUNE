"""Tests for the tune_dms package (config only). No GUI or network."""

import pytest

from tune_dms.config import TuneConfig


class TestTuneConfig:
    """TuneConfig construction and validation."""

    def test_from_env_defaults_without_env(self, monkeypatch):
        monkeypatch.delenv("TUNE_USER_ID", raising=False)
        monkeypatch.delenv("TUNE_USER_PASSWORD", raising=False)
        monkeypatch.delenv("TUNE_SHORTCUT_PATH", raising=False)
        monkeypatch.delenv("TUNE_IMAGES_DIR", raising=False)
        monkeypatch.delenv("TUNE_REPORTS_DIR", raising=False)
        config = TuneConfig.from_env(load_dotenv=False)
        assert config.user_id == ""
        assert config.password == ""
        assert "TUNE" in config.shortcut_path

    def test_from_env_explicit_overrides(self, monkeypatch):
        monkeypatch.delenv("TUNE_USER_ID", raising=False)
        monkeypatch.delenv("TUNE_USER_PASSWORD", raising=False)
        config = TuneConfig.from_env(
            user_id="uid",
            password="pwd",
            load_dotenv=False,
        )
        assert config.user_id == "uid"
        assert config.password == "pwd"

    def test_validate_raises_when_empty_credentials(self):
        config = TuneConfig(
            user_id="",
            password="",
        )
        with pytest.raises(ValueError, match="TUNE_USER_ID and TUNE_USER_PASSWORD"):
            config.validate()

    def test_validate_passes_with_credentials(self):
        config = TuneConfig(
            user_id="u",
            password="p",
        )
        config.validate()
