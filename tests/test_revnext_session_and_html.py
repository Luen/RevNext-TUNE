"""
Session cookie jar loading and HTML response diagnostics for revnext.

Run: python -m unittest tests.test_revnext_session_and_html
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "revnext"))

from revnext.common import (
    _body_snippet,
    _error_suggests_relogin,
    _looks_like_html,
    _parse_json_response,
)
from revnext.notifications import _notifications_from_response
from revnext.session import (
    _apply_cookies,
    is_login_page_bytes,
    load_session,
    save_session,
)


class HtmlDetectionTests(unittest.TestCase):
    def test_html_doctype_is_detected(self):
        self.assertTrue(_looks_like_html(b"<!DOCTYPE html><html>"))

    def test_json_is_not_html(self):
        self.assertFalse(_looks_like_html(b'{"ok": true}'))

    def test_login_page_bytes(self):
        body = b"<html><body>Please sign in to REVOLUTIONnext</body></html>"
        self.assertTrue(is_login_page_bytes(body))

    def test_parse_json_includes_context_for_html(self):
        response = MagicMock()
        response.content = b"<!DOCTYPE html><html>oops</html>"
        response.url = "https://example.test/next/rest/si/static/submitActivityTask"
        response.status_code = 200
        response.headers = {"Content-Type": "text/html"}
        with self.assertRaises(ValueError) as ctx:
            _parse_json_response(response)
        message = str(ctx.exception)
        self.assertIn("looks like HTML", message)
        self.assertIn("status=200", message)
        self.assertIn("submitActivityTask", message)

    def test_error_suggests_relogin_for_html(self):
        self.assertTrue(
            _error_suggests_relogin(
                ValueError("Response body looks like HTML (login page); url=...")
            )
        )

    def test_body_snippet_collapses_whitespace(self):
        self.assertEqual(_body_snippet(b"a\n  b\tc"), "a b c")


class SessionCookieJarTests(unittest.TestCase):
    def test_load_session_puts_cookies_in_jar_not_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            path.write_text(
                json.dumps(
                    {
                        "domain": "mikecarney.revolutionnext.com.au",
                        "cookies": [["JSESSIONID", "abc"], ["OTHER", "xyz"]],
                    }
                ),
                encoding="utf-8",
            )
            session = load_session(
                "https://mikecarney.revolutionnext.com.au", path, timeout=5
            )
            self.assertIsNotNone(session)
            assert session is not None
            self.assertNotIn("cookie", {k.lower() for k in session.headers})
            names = {c.name: c.value for c in session.cookies}
            self.assertEqual(names["JSESSIONID"], "abc")
            self.assertEqual(names["OTHER"], "xyz")

    def test_save_round_trip_keeps_jar_cookies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            from revnext.common import new_session

            session = new_session(5)
            _apply_cookies(session, [["JSESSIONID", "roundtrip"]])
            save_session(session, "https://mikecarney.revolutionnext.com.au", path)
            loaded = load_session(
                "https://mikecarney.revolutionnext.com.au", path, timeout=5
            )
            assert loaded is not None
            self.assertEqual(
                {c.name: c.value for c in loaded.cookies}["JSESSIONID"], "roundtrip"
            )


class NotificationParseTests(unittest.TestCase):
    def test_extracts_notification_rows(self):
        payload = {
            "dataSets": [
                {
                    "name": "responseData",
                    "dataSet": {
                        "responseData": {
                            "header": [{"count": 1, "unread": 2}],
                            "notification": [
                                {
                                    "subject": "The Parts Price List is ready to download",
                                    "url": "web/Spark/...?taskID=abc-123",
                                    "x_rowid": "AAAA",
                                }
                            ],
                        }
                    },
                }
            ]
        }
        rows = _notifications_from_response(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["x_rowid"], "AAAA")


if __name__ == "__main__":
    unittest.main()
