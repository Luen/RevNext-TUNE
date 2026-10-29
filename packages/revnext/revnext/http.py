"""
HTTP helpers for Revolution Next REST calls: timed sessions, JSON parse, retries.
"""

import json
import time

import requests

from revnext.config import DEFAULT_TIMEOUT, timeout_from_env
from revnext.logger import get_logger

logger = get_logger(__name__)

# Minimum response length to consider as valid JSON (e.g. "{}").
MIN_JSON_BODY_LENGTH = 2


class TimeoutSession(requests.Session):
    """A requests Session that applies a default timeout to every request.

    Setting it here rather than at each call site means a new request cannot
    silently be written without one. An explicit ``timeout=`` still wins.
    """

    def __init__(self, timeout: float | tuple[float, float] = DEFAULT_TIMEOUT):
        super().__init__()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, url, **kwargs)


def new_session(
    timeout: float | tuple[float, float] | None = None,
) -> requests.Session:
    """Create a session that times out by default.

    timeout: seconds, or a (connect, read) pair. Defaults to REVNEXT_TIMEOUT if set,
    else DEFAULT_TIMEOUT.
    """
    return TimeoutSession(timeout if timeout is not None else timeout_from_env())


class ReportDownloadError(RuntimeError):
    """
    Raised when the report API returns invalid, empty, or non-JSON (e.g. HTML)
    after all retry attempts. Consumers can catch this to distinguish transient
    API failures from other errors.
    """


def _looks_like_html(content: bytes) -> bool:
    """True if the response body looks like HTML (error page, login redirect, etc.)."""
    if not content or len(content) < 2:
        return False
    start = content.lstrip()[:200]
    try:
        text = start.decode("utf-8", errors="replace").strip().lower()
    except (UnicodeDecodeError, AttributeError):
        return False
    return text.startswith("<!") or "<html" in text[:50]


def _body_snippet(content: bytes | None, limit: int = 200) -> str:
    """Short printable prefix of a response body for logs."""
    if not content:
        return ""
    text = content.lstrip()[:limit].decode("utf-8", errors="replace")
    return " ".join(text.split())


def _response_error_context(response: requests.Response | None) -> str:
    """URL / status / content-type / body snippet for failed API responses."""
    if response is None:
        return "no response"
    content_type = response.headers.get("Content-Type", "")
    return (
        f"url={response.url!r} status={response.status_code} "
        f"content-type={content_type!r} body={_body_snippet(response.content)!r}"
    )


def _error_suggests_relogin(error: BaseException) -> bool:
    """True when a failure looks like an expired session / login HTML page."""
    text = str(error).lower()
    return any(
        needle in text
        for needle in (
            "looks like html",
            "login redirect",
            "j_username",
            "sign in to revolutionnext",
        )
    )


def _common_headers(base_url: str) -> dict:
    """Build common request headers for the given base URL."""
    return {
        "accept": "*/*",
        "accept-language": "en-AU,en-US;q=0.9,en-GB;q=0.8,en;q=0.7",
        "content-type": "application/json; charset=UTF-8",
        "origin": base_url,
        "referrer": f"{base_url}/next/Fluid.html?useTabs",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    }


def _parse_json_response(
    response: requests.Response,
    min_length: int = MIN_JSON_BODY_LENGTH,
) -> dict:
    """
    Parse response body as JSON. Raises ValueError if body is empty, too small,
    looks like HTML, or is invalid JSON. Used by retry logic to detect transient failures.
    """
    content = response.content
    if content is None or len(content) < min_length:
        raise ValueError(
            f"Response body empty or too small (length {len(content) if content else 0}, "
            f"expected at least {min_length} for valid JSON); {_response_error_context(response)}"
        )
    if _looks_like_html(content):
        from revnext.session import is_login_page_bytes

        kind = "login page" if is_login_page_bytes(content) else "error/redirect page"
        raise ValueError(
            f"Response body looks like HTML ({kind}); {_response_error_context(response)}"
        )
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Response is not valid JSON: {e}; {_response_error_context(response)}"
        ) from e


def _post_json_with_retry(
    session: requests.Session,
    url: str,
    *,
    max_attempts: int,
    retry_delay: float,
    report_label: str | None,
    step_name: str,
    **kwargs,
) -> dict:
    """
    POST and parse JSON with retries. On empty/HTML/JSONDecodeError, log and retry.
    After last attempt, raise ReportDownloadError.
    """
    last_error = None
    last_response: requests.Response | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.post(url, **kwargs)
            last_response = r
            r.raise_for_status()
            return _parse_json_response(r)
        except (ValueError, json.JSONDecodeError) as e:
            last_error = e
            reason = str(e)
        except requests.RequestException as e:
            last_error = e
            reason = str(e)
            last_response = getattr(e, "response", None)
        if attempt < max_attempts:
            prefix = f"[{report_label}] " if report_label else ""
            logger.warning(
                "%s%s attempt %d of %d failed (%s); retrying in %.1fs. %s",
                prefix,
                step_name,
                attempt,
                max_attempts,
                reason,
                retry_delay,
                _response_error_context(last_response),
            )
            time.sleep(retry_delay)
        else:
            break
    label_suffix = f" [{report_label}]" if report_label else ""
    raise ReportDownloadError(
        f"Report API returned invalid or non-JSON response after {max_attempts} attempt(s)"
        f"{label_suffix}: {last_error}"
    ) from last_error


def _get_content_with_retry(
    session: requests.Session,
    url: str,
    *,
    max_attempts: int,
    retry_delay: float,
    report_label: str | None,
    step_name: str,
    min_content_length: int = 1,
) -> bytes:
    """
    GET report content (e.g. CSV) with retries. Retries when body is empty or looks like HTML.
    After last attempt, raise ReportDownloadError.
    """
    last_error = None
    last_response: requests.Response | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(url)
            last_response = r
            r.raise_for_status()
            content = r.content or b""
            if len(content) < min_content_length:
                raise ValueError(
                    f"Response body empty or too small (length {len(content)}); "
                    f"{_response_error_context(r)}"
                )
            if _looks_like_html(content):
                from revnext.session import is_login_page_bytes

                kind = (
                    "login page"
                    if is_login_page_bytes(content)
                    else "error/redirect page"
                )
                raise ValueError(
                    f"Response body looks like HTML ({kind}); {_response_error_context(r)}"
                )
            return content
        except (ValueError, requests.RequestException) as e:
            last_error = e
            reason = str(e)
            if isinstance(e, requests.RequestException):
                last_response = getattr(e, "response", None)
        if attempt < max_attempts:
            prefix = f"[{report_label}] " if report_label else ""
            logger.warning(
                "%s%s attempt %d of %d failed (%s); retrying in %.1fs. %s",
                prefix,
                step_name,
                attempt,
                max_attempts,
                reason,
                retry_delay,
                _response_error_context(last_response),
            )
            time.sleep(retry_delay)
        else:
            break
    label_suffix = f" [{report_label}]" if report_label else ""
    raise ReportDownloadError(
        f"Report download returned invalid or empty content after {max_attempts} attempt(s)"
        f"{label_suffix}: {last_error}"
    ) from last_error
