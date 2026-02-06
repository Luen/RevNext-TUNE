"""Tests for the revnext package (config and pure helpers). No network calls."""

import pytest

from revnext.common import (
    extract_task_id,
    get_response_url_from_load_data,
    is_poll_done,
)
from revnext.config import RevNextConfig, get_revnext_base_url_from_env


class TestRevNextConfig:
    """RevNextConfig construction and validation."""

    def test_from_env_defaults_without_env(self, monkeypatch):
        monkeypatch.delenv("REVNEXT_URL", raising=False)
        monkeypatch.delenv("REVNEXT_USERNAME", raising=False)
        monkeypatch.delenv("REVNEXT_PASSWORD", raising=False)
        monkeypatch.delenv("REVNEXT_SESSION_PATH", raising=False)
        config = RevNextConfig.from_env(load_dotenv=False)
        assert config.base_url.startswith("https://")
        assert config.username == ""
        assert config.password == ""
        assert config.session_path is not None

    def test_from_env_explicit_overrides(self, monkeypatch):
        monkeypatch.delenv("REVNEXT_USERNAME", raising=False)
        monkeypatch.delenv("REVNEXT_PASSWORD", raising=False)
        config = RevNextConfig.from_env(
            base_url="https://example.revolutionnext.com.au",
            username="u",
            password="p",
            load_dotenv=False,
        )
        assert config.base_url == "https://example.revolutionnext.com.au"
        assert config.username == "u"
        assert config.password == "p"

    def test_validate_raises_when_empty_credentials(self):
        config = RevNextConfig(
            base_url="https://x.revolutionnext.com.au",
            username="",
            password="",
        )
        with pytest.raises(ValueError, match="REVNEXT_USERNAME and REVNEXT_PASSWORD"):
            config.validate()

    def test_validate_passes_with_credentials(self):
        config = RevNextConfig(
            base_url="https://x.revolutionnext.com.au",
            username="u",
            password="p",
        )
        config.validate()


class TestGetRevNextBaseUrlFromEnv:
    def test_returns_default_without_env(self, monkeypatch):
        monkeypatch.delenv("REVNEXT_URL", raising=False)
        url = get_revnext_base_url_from_env()
        assert url.startswith("https://")

    def test_adds_https_if_missing(self, monkeypatch):
        monkeypatch.setenv("REVNEXT_URL", "mikecarney.revolutionnext.com.au")
        url = get_revnext_base_url_from_env()
        assert url.startswith("https://")


class TestExtractTaskId:
    """extract_task_id from submitActivityTask response."""

    def test_extracts_task_id(self):
        data = {
            "dataSets": [
                {
                    "name": "dsActivityTask",
                    "dataSet": {
                        "dsActivityTask": {
                            "ttActivityTask": [{"taskID": "abc-123"}],
                        }
                    },
                }
            ]
        }
        assert extract_task_id(data) == "abc-123"

    def test_returns_none_when_missing(self):
        assert extract_task_id({}) is None
        assert extract_task_id({"dataSets": []}) is None
        assert extract_task_id({"dataSets": [{"name": "other", "dataSet": {}}]}) is None


class TestIsPollDone:
    """is_poll_done from autoPollResponse."""

    def test_true_when_auto_poll_minus_one(self):
        data = {"ctrlProp": [{"name": "button.autoPollResponse", "value": "-1"}]}
        assert is_poll_done(data) is True

    def test_false_when_other_value(self):
        data = {"ctrlProp": [{"name": "button.autoPollResponse", "value": "0"}]}
        assert is_poll_done(data) is False

    def test_false_when_empty(self):
        assert is_poll_done({}) is False


class TestGetResponseUrlFromLoadData:
    """get_response_url_from_load_data from loadData response."""

    def test_extracts_response_url(self):
        data = {
            "dataSets": [
                {
                    "name": "dsActivityTask",
                    "dataSet": {
                        "dsActivityTask": {
                            "ttActivityTaskResponse": [
                                {"responseUrl": "/next/output/report.csv"}
                            ],
                        }
                    },
                }
            ]
        }
        assert get_response_url_from_load_data(data) == "/next/output/report.csv"

    def test_returns_none_when_missing(self):
        assert get_response_url_from_load_data({}) is None
