"""
Auto-login and session persistence for Revolution Next (*.revolutionnext.com.au).
Login via j_spring_security_check; persist cookies to disk; validate before use and re-login if needed.
"""

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from revnext.common import _common_headers, new_session
from revnext.config import RevNextConfig
from revnext.logger import get_logger

logger = get_logger(__name__)


def _login_page_url(base_url: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", "next/Fluid.html")


def _security_check_url(base_url: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", "next/j_spring_security_check")


def _form_action_url(html: str, current_page_url: str) -> str | None:
    """Get form action URL from login page HTML, resolved against the current page URL (after redirects)."""
    m = re.search(
        r'<form[^>]+action=["\']([^"\']*)["\']', html, re.IGNORECASE | re.DOTALL
    )
    if not m:
        m = re.search(r'action=["\']([^"\']*)["\']', html)
    if m:
        return urljoin(current_page_url, m.group(1).strip())
    return None


def _extract_csrf(html: str) -> str | None:
    """Extract CSRF token from login page HTML. Tries several patterns (quotes, attribute order)."""
    patterns = [
        r'name=["\']CSRFToken["\'][^>]*value=["\']([^"\']+)["\']',
        r'value=["\']([^"\']+)["\'][^>]*name=["\']CSRFToken["\']',
        r"name=CSRFToken\s+value=([^\s>]+)",
        r"value=([^\s>]+)\s+name=CSRFToken",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def login(
    base_url: str,
    username: str,
    password: str,
    timeout: float | tuple[float, float] | None = None,
) -> requests.Session:
    """
    Log in to Revolution Next: GET login page for CSRF and session cookie, POST to j_spring_security_check.
    Returns a requests.Session with auth cookies set; every request on it carries a timeout.
    """
    session = new_session(timeout)
    session.headers.update(_common_headers(base_url))

    login_url = _login_page_url(base_url)
    r = session.get(login_url, timeout=30, allow_redirects=True)
    r.raise_for_status()
    csrf = _extract_csrf(r.text)
    if not csrf:
        raise ValueError(
            "CSRF token not found on login page; page may have changed or URL may be wrong."
        )
    # POST to the form action URL (resolve from final page URL so /next/static/auth/j_spring_security_check works)
    check_url = _form_action_url(r.text, r.url) or _security_check_url(base_url)
    r2 = session.post(
        check_url,
        data={
            "j_username": username,
            "j_password": password,
            "CSRFToken": csrf,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=True,
        timeout=30,
    )
    r2.raise_for_status()
    if _is_login_page(r2.text):
        raise ValueError(
            "Login failed: still on login page after POST (check username/password)."
        )
    return session


def _is_login_page(html: str) -> bool:
    """True if the response body looks like the login form."""
    return "sign in to REVOLUTIONnext" in html or 'name="j_username"' in html


def is_login_page_bytes(content: bytes) -> bool:
    """True if response bytes look like the RevNext login HTML page."""
    if not content:
        return False
    try:
        text = content.lstrip()[:2000].decode("utf-8", errors="replace")
    except (UnicodeDecodeError, AttributeError):
        return False
    return _is_login_page(text)


def is_session_valid(session: requests.Session, base_url: str) -> bool:
    """
    Check if the session is still valid by GETting the app and ensuring we are not on the login page.
    """
    try:
        url = _login_page_url(base_url)
        r = session.get(url, timeout=15)
        r.raise_for_status()
        return not _is_login_page(r.text)
    except requests.RequestException:
        # Any transport or HTTP failure means we cannot vouch for the session.
        return False


def _session_file_format(domain: str, session: requests.Session) -> dict:
    """Build a JSON-serialisable dict of domain and cookie name/value pairs."""
    pairs = [[c.name, c.value] for c in session.cookies]
    return {"domain": domain, "cookies": pairs}


def _apply_cookies(session: requests.Session, pairs: list[list[str]]) -> None:
    """Load cookies into the jar only (never a static Cookie header).

    A static Cookie header overrides the jar and ignores Set-Cookie updates, so
    mid-session rotations (and save_session after load) would keep dead cookies.
    """
    session.headers.pop("cookie", None)
    session.headers.pop("Cookie", None)
    for name, value in pairs:
        if isinstance(name, str) and isinstance(value, str):
            session.cookies.set(name, value)


def save_session(session: requests.Session, base_url: str, path: Path) -> None:
    """Persist session cookies to a JSON file for the given base URL domain."""
    parsed = urlparse(base_url)
    domain = parsed.netloc or parsed.path
    if not domain:
        raise ValueError(f"Invalid base_url: {base_url}")
    data = _session_file_format(domain, session)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def invalidate_session_file(path: Path | None) -> None:
    """Remove a persisted session file so the next login cannot reuse it."""
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError as e:
        logger.warning("Could not remove session file %s: %s", path, e)


def load_session(
    base_url: str,
    path: Path,
    timeout: float | tuple[float, float] | None = None,
) -> requests.Session | None:
    """
    Load a session from a previously saved JSON file. Returns None if file missing or invalid.
    The returned session carries a default timeout on every request.
    """
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    domain = data.get("domain")
    cookies = data.get("cookies")
    if not domain or not isinstance(cookies, list):
        return None
    parsed = urlparse(base_url)
    want_domain = parsed.netloc or parsed.path
    if not want_domain or (
        domain != want_domain and not want_domain.endswith("." + domain.lstrip("."))
    ):
        return None
    session = new_session(timeout)
    session.headers.update(_common_headers(base_url))
    _apply_cookies(
        session,
        [[n, v] for n, v in cookies if isinstance(n, str) and isinstance(v, str)],
    )
    return session


def get_or_create_session(
    config: RevNextConfig, service_object: str
) -> requests.Session:
    """
    Return an authenticated session: load from config.session_path if present and valid,
    otherwise log in with config username/password, save session to disk, and return it.
    Session has common headers and x-service-object set.
    """
    config.validate()
    base_url = config.base_url
    path = config.session_path or Path.cwd() / ".revnext-session.json"

    session = load_session(base_url, path, config.timeout)
    if session and is_session_valid(session, base_url):
        session.headers["x-service-object"] = service_object
        return session

    session = login(base_url, config.username, config.password, config.timeout)
    save_session(session, base_url, path)
    session.headers["x-service-object"] = service_object
    return session


def force_relogin(config: RevNextConfig, service_object: str) -> requests.Session:
    """Drop any persisted session and log in again. Use when API responses look like login HTML."""
    config.validate()
    path = config.session_path or Path.cwd() / ".revnext-session.json"
    invalidate_session_file(path)
    logger.warning("Re-logging in to RevNext (session invalidated at %s).", path)
    session = login(config.base_url, config.username, config.password, config.timeout)
    save_session(session, config.base_url, path)
    session.headers["x-service-object"] = service_object
    return session
