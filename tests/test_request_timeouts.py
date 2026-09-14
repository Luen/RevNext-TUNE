"""
Every request the revnext package makes must carry a timeout.

requests defaults to none, so a server that accepts the connection and then never
answers blocks the caller forever - no retry, no error, no log line. That wedged a
nightly sync in production for two hours.

Run: python -m unittest tests.test_request_timeouts
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "revnext"))

from revnext.common import TimeoutSession, new_session
from revnext.config import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
    RevNextConfig,
    parse_timeout,
    timeout_from_env,
)


class ParseTimeoutTests(unittest.TestCase):
    def test_single_number_is_the_read_timeout(self):
        self.assertEqual(parse_timeout("30"), (DEFAULT_CONNECT_TIMEOUT, 30.0))

    def test_pair_is_connect_then_read(self):
        self.assertEqual(parse_timeout("5,60"), (5.0, 60.0))

    def test_whitespace_is_tolerated(self):
        self.assertEqual(parse_timeout("  5 , 60 "), (5.0, 60.0))

    def test_unparseable_input_falls_back_rather_than_disabling_the_timeout(self):
        """A bad value must not be read as "no timeout" - that is the bug we are fixing."""
        for bad in ("", "   ", "nonsense", "1,2,3", ","):
            self.assertIsNone(parse_timeout(bad), bad)

    def test_none(self):
        self.assertIsNone(parse_timeout(None))


class TimeoutFromEnvTests(unittest.TestCase):
    def test_default_when_unset(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("REVNEXT_TIMEOUT", None)
            self.assertEqual(timeout_from_env(), DEFAULT_TIMEOUT)

    def test_env_override(self):
        with patch.dict("os.environ", {"REVNEXT_TIMEOUT": "3,45"}):
            self.assertEqual(timeout_from_env(), (3.0, 45.0))

    def test_bad_env_value_keeps_the_default(self):
        with patch.dict("os.environ", {"REVNEXT_TIMEOUT": "not-a-number"}):
            self.assertEqual(timeout_from_env(), DEFAULT_TIMEOUT)


class SessionTimeoutTests(unittest.TestCase):
    def _captured_timeout(self, session, **kwargs):
        """The timeout the session hands down to requests.Session.request."""
        with patch.object(requests.Session, "request", autospec=True) as mocked:
            type(session).request(session, "GET", "https://example.invalid", **kwargs)
            return mocked.call_args.kwargs.get("timeout")

    def test_a_plain_requests_session_sends_no_timeout(self):
        """The bug this guards against: requests waits forever by default."""
        self.assertIsNone(self._captured_timeout(requests.Session()))

    def test_default_timeout_is_applied(self):
        self.assertEqual(self._captured_timeout(new_session()), DEFAULT_TIMEOUT)

    def test_explicit_timeout_wins(self):
        self.assertEqual(self._captured_timeout(new_session(), timeout=2), 2)

    def test_session_timeout_is_configurable(self):
        self.assertEqual(self._captured_timeout(new_session((1, 2))), (1, 2))

    def test_new_session_is_a_requests_session(self):
        session = new_session()
        self.assertIsInstance(session, requests.Session)
        self.assertIsInstance(session, TimeoutSession)


class ConfigTimeoutTests(unittest.TestCase):
    def test_config_carries_a_timeout_by_default(self):
        config = RevNextConfig(base_url="https://x", username="u", password="p")
        self.assertEqual(config.timeout, DEFAULT_TIMEOUT)

    def test_from_env_explicit_override(self):
        config = RevNextConfig.from_env(
            base_url="https://x", username="u", password="p", timeout=(2, 3)
        )
        self.assertEqual(config.timeout, (2, 3))

    def test_from_env_reads_the_env_var(self):
        with patch.dict("os.environ", {"REVNEXT_TIMEOUT": "4,44"}):
            config = RevNextConfig.from_env(
                base_url="https://x", username="u", password="p", load_dotenv=False
            )
            self.assertEqual(config.timeout, (4.0, 44.0))


if __name__ == "__main__":
    unittest.main()
