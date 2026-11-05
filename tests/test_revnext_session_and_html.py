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
from unittest.mock import MagicMock, patch

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
    _extract_csrf,
    _looks_like_app_shell,
    is_login_page_bytes,
    load_session,
    login,
    save_session,
)

# Realistic login.jsp: long <head> then form (CSRF / j_username past the old 2KB scan).
_LONG_HEAD = "x" * 2500
_REALISTIC_LOGIN_HTML = f"""<!DOCTYPE HTML>
<head><title>REVOLUTIONnext SmartCenter</title>
<meta name="padding" content="{_LONG_HEAD}" />
</head>
<body>
<form role="form" name="Login" action="j_spring_security_check" method="post">
<input type="hidden" value='11f5c304-8530-4182-b133-0b233c6f6853' name="CSRFToken">
<h4>Use the form below to sign in to REVOLUTIONnext</h4>
<input name="j_username" id="userField" type="text" value="">
<input name="j_password" id="passwordField" type="password" value="">
</form>
</body>
</html>
"""


class HtmlDetectionTests(unittest.TestCase):
    def test_html_doctype_is_detected(self):
        self.assertTrue(_looks_like_html(b"<!DOCTYPE html><html>"))

    def test_json_is_not_html(self):
        self.assertFalse(_looks_like_html(b'{"ok": true}'))

    def test_login_page_bytes(self):
        body = b"<html><body>Please sign in to REVOLUTIONnext</body></html>"
        self.assertTrue(is_login_page_bytes(body))

    def test_login_page_bytes_with_long_head(self):
        body = _REALISTIC_LOGIN_HTML.encode("utf-8")
        self.assertGreater(body.find(b"CSRFToken"), 2000)
        self.assertTrue(is_login_page_bytes(body))

    def test_extract_csrf_value_before_name_single_quotes(self):
        html = (
            "<input type=\"hidden\" value='11f5c304-8530-4182-b133-0b233c6f6853' "
            'name="CSRFToken">'
        )
        self.assertEqual(_extract_csrf(html), "11f5c304-8530-4182-b133-0b233c6f6853")

    def test_extract_csrf_name_before_value(self):
        html = '<input type="hidden" name="CSRFToken" value="abc-def">'
        self.assertEqual(_extract_csrf(html), "abc-def")

    def test_extract_csrf_from_realistic_login_html(self):
        self.assertEqual(
            _extract_csrf(_REALISTIC_LOGIN_HTML),
            "11f5c304-8530-4182-b133-0b233c6f6853",
        )

    def test_app_shell_without_csrf(self):
        spa = (
            "<!DOCTYPE html><html><head>"
            '<meta http-equiv="content-type" content="text/html; charset=UTF-8">'
            "<title>Revolution</title></head><body></body></html>"
        )
        self.assertTrue(_looks_like_app_shell(spa))
        self.assertIsNone(_extract_csrf(spa))
        self.assertFalse(_looks_like_app_shell(_REALISTIC_LOGIN_HTML))

    def test_login_retries_after_app_shell(self):
        spa = MagicMock(
            text=(
                "<!DOCTYPE html><html><head><title>Revolution</title></head>"
                "<body></body></html>"
            ),
            content=(
                b"<!DOCTYPE html><html><head><title>Revolution</title></head>"
                b"<body></body></html>"
            ),
            url="https://example.test/next/Fluid.html",
            status_code=200,
            raise_for_status=MagicMock(),
        )
        form = MagicMock(
            text=_REALISTIC_LOGIN_HTML,
            content=_REALISTIC_LOGIN_HTML.encode("utf-8"),
            url="https://example.test/next/static/auth/login.jsp",
            status_code=200,
            raise_for_status=MagicMock(),
        )
        post_ok = MagicMock(
            text="<html><body>ok</body></html>",
            status_code=200,
            raise_for_status=MagicMock(),
        )
        mock_session = MagicMock()
        mock_session.cookies = MagicMock()
        mock_session.headers = {}
        mock_session.get.side_effect = [spa, form]
        mock_session.post.return_value = post_ok

        with (
            patch("revnext.session.new_session", return_value=mock_session),
            patch("revnext.session._common_headers", return_value={}),
        ):
            result = login("https://example.test", "user", "pass", timeout=5)

        self.assertIs(result, mock_session)
        self.assertEqual(mock_session.get.call_count, 2)
        mock_session.cookies.clear.assert_called_once()
        mock_session.post.assert_called_once()
        posted_data = mock_session.post.call_args.kwargs["data"]
        self.assertEqual(
            posted_data,
            {
                "j_username": "user",
                "j_password": "pass",
                "CSRFToken": "11f5c304-8530-4182-b133-0b233c6f6853",
            },
        )

    def test_parse_json_classifies_realistic_login_as_login_page(self):
        response = MagicMock()
        response.content = _REALISTIC_LOGIN_HTML.encode("utf-8")
        response.url = "https://example.test/next/static/auth/login.jsp"
        response.status_code = 200
        response.headers = {"Content-Type": "text/html;charset=UTF-8"}
        with self.assertRaises(ValueError) as ctx:
            _parse_json_response(response)
        self.assertIn("login page", str(ctx.exception))

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

    def test_error_suggests_login_page_excludes_generic_html(self):
        from revnext.http import _error_suggests_login_page

        self.assertTrue(
            _error_suggests_login_page(
                ValueError("Response body looks like HTML (login page); url=...")
            )
        )
        self.assertFalse(
            _error_suggests_login_page(
                ValueError(
                    "Response body looks like HTML (error/redirect page); url=..."
                )
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


class ActivityTabAndMidStepReloginTests(unittest.TestCase):
    def test_new_activity_tab_id_matches_browser_shape(self):
        from revnext.report_flow import new_activity_tab_id

        tab_id = new_activity_tab_id()
        self.assertTrue(tab_id.startswith("N"))
        self.assertNotIn("-", tab_id)
        self.assertEqual(tab_id.count("_"), 4)
        self.assertNotEqual(new_activity_tab_id(), tab_id)

    def test_post_retry_relogins_on_login_html(self):
        from revnext.http import SessionSlot, _post_json_with_retry

        first = MagicMock()
        first.post.return_value = MagicMock(
            content=b"<!DOCTYPE html><html>sign in to REVOLUTIONnext j_username</html>",
            url="https://example.test/submit",
            status_code=200,
            headers={"Content-Type": "text/html"},
            raise_for_status=MagicMock(),
        )
        second = MagicMock()
        ok = MagicMock(
            content=b'{"ok": true}',
            url="https://example.test/submit",
            status_code=201,
            headers={"Content-Type": "application/json"},
            raise_for_status=MagicMock(),
        )
        ok.json.return_value = {"ok": True}
        second.post.return_value = ok

        slot = SessionSlot(first)
        calls = {"n": 0}

        def relogin():
            calls["n"] += 1
            return second

        result = _post_json_with_retry(
            slot,
            "https://example.test/submit",
            max_attempts=3,
            retry_delay=0,
            report_label="test",
            step_name="submit",
            relogin=relogin,
            json={},
        )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls["n"], 1)
        self.assertIs(slot.session, second)


if __name__ == "__main__":
    unittest.main()
