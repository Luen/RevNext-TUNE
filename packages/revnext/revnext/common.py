"""
Shared utilities for Revolution Next (*.revolutionnext.com.au) report downloads.
Session creation (auto-login with persistence) and generic submit → poll → loadData → download flow.
"""

import json
import time
from pathlib import Path
from typing import Callable

import requests

from revnext.config import RevNextConfig
from revnext.logger import get_logger

logger = get_logger(__name__)

# Minimum response length to consider as valid JSON (e.g. "{}").
MIN_JSON_BODY_LENGTH = 2


class ReportDownloadError(RuntimeError):
    """
    Raised when the report API returns invalid, empty, or non-JSON (e.g. HTML)
    after all retry attempts. Consumers can catch this to distinguish transient
    API failures from other errors.
    """

    pass


def _looks_like_html(content: bytes) -> bool:
    """True if the response body looks like HTML (error page, login redirect, etc.)."""
    if not content or len(content) < 2:
        return False
    start = content.lstrip()[:200]
    try:
        text = start.decode("utf-8", errors="replace").strip().lower()
    except Exception:
        return False
    return text.startswith("<!") or "<html" in text[:50]


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
            f"expected at least {min_length} for valid JSON)"
        )
    if _looks_like_html(content):
        raise ValueError(
            "Response body looks like HTML (error page, login redirect, or 502/503 page)"
        )
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON: {e}") from e


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
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.post(url, **kwargs)
            r.raise_for_status()
            return _parse_json_response(r)
        except (ValueError, json.JSONDecodeError) as e:
            last_error = e
            reason = str(e)
        except requests.RequestException as e:
            last_error = e
            reason = str(e)
        if attempt < max_attempts:
            prefix = f"[{report_label}] " if report_label else ""
            logger.warning(
                "%s%s attempt %d of %d failed (%s); retrying in %.1fs.",
                prefix,
                step_name,
                attempt,
                max_attempts,
                reason,
                retry_delay,
            )
            time.sleep(retry_delay)
        else:
            break
    label_suffix = f" [{report_label}]" if report_label else ""
    raise ReportDownloadError(
        f"Report API returned invalid or non-JSON response after {max_attempts} attempt(s){label_suffix}: {last_error}"
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
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(url)
            r.raise_for_status()
            content = r.content or b""
            if len(content) < min_content_length:
                raise ValueError(
                    f"Response body empty or too small (length {len(content)})"
                )
            if _looks_like_html(content):
                raise ValueError("Response body looks like HTML (error/redirect page)")
            return content
        except (ValueError, requests.RequestException) as e:
            last_error = e
            reason = str(e)
        if attempt < max_attempts:
            prefix = f"[{report_label}] " if report_label else ""
            logger.warning(
                "%s%s attempt %d of %d failed (%s); retrying in %.1fs.",
                prefix,
                step_name,
                attempt,
                max_attempts,
                reason,
                retry_delay,
            )
            time.sleep(retry_delay)
        else:
            break
    label_suffix = f" [{report_label}]" if report_label else ""
    raise ReportDownloadError(
        f"Report download returned invalid or empty content after {max_attempts} attempt(s){label_suffix}: {last_error}"
    ) from last_error


def get_or_create_session(
    config: RevNextConfig, service_object: str
) -> requests.Session:
    """
    Return an authenticated session: load from config.session_path if present and valid,
    otherwise log in with config username/password, save session to disk, and return it.
    """
    from revnext.session import get_or_create_session as _get_or_create_session

    return _get_or_create_session(config, service_object)


def extract_task_id(submit_response: dict) -> str | None:
    """Extract taskID from submitActivityTask response."""
    for ds in submit_response.get("dataSets", []):
        if ds.get("name") != "dsActivityTask":
            continue
        d = ds.get("dataSet", {}).get("dsActivityTask", {})
        for row in d.get("ttActivityTask", []):
            tid = row.get("taskID")
            if tid:
                return tid
    return None


def is_poll_done(poll_response: dict) -> bool:
    """True when report is ready (autoPollResponse returns -1)."""
    for cp in poll_response.get("ctrlProp", []):
        if cp.get("name") == "button.autoPollResponse" and cp.get("value") == "-1":
            return True
    return False


def get_response_url_from_load_data(load_data: dict) -> str | None:
    """Extract responseUrl from loadData response (ttActivityTaskResponse)."""
    for ds in load_data.get("dataSets", []):
        if ds.get("name") != "dsActivityTask":
            continue
        d = ds.get("dataSet", {}).get("dsActivityTask", {})
        for row in d.get("ttActivityTaskResponse", []):
            url = row.get("responseUrl")
            if url:
                return url
    return None


def _has_submit_errors(response_data: dict) -> tuple[bool, bool]:
    """Return (has_error, has_warning_only). If has_error, raise after building message."""
    error_table = response_data.get("errorTable") or []
    has_error = any(e.get("type") == "ERROR" for e in error_table)
    has_warning = any(e.get("type") == "WARNING" for e in error_table)
    return has_error, has_warning and not has_error


def _submit_errors_message(response_data: dict) -> str:
    """Build a single message from errorTable entries."""
    parts = []
    for e in response_data.get("errorTable") or []:
        msg = e.get("msg") or e.get("type", "")
        if msg:
            parts.append(msg)
    return "; ".join(parts) if parts else "Unknown error"


def run_report_flow(
    session: requests.Session,
    service_object: str,
    activity_tab_id: str,
    get_submit_body: Callable[[], dict],
    base_url: str,
    output_path: Path | None = None,
    post_submit_hook: Callable[[requests.Session], None] | None = None,
    max_polls: int = 60,
    poll_interval: float = 2,
    report_label: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5,
) -> Path | bytes:
    """
    Submit report task, poll until ready, loadData for download URL, then download CSV.
    On submit: if response has ERROR, raises; if only WARNING and not success, retries once with stopOnWarning=False.
    Optionally call post_submit_hook(session) after submit (e.g. onChoose_btn_closesubmit).
    If output_path is set: save content to file and return the Path.
    If output_path is None: return the report content as bytes (caller can save or load into pandas).
    report_label: optional short label (e.g. "Parts Price List - 130") included in poll/complete messages.
    max_retries: number of attempts per API request when response is empty, HTML, or invalid JSON (default 3).
    retry_delay: seconds to wait between retries (default 5). Raises ReportDownloadError after last attempt.
    """
    submit_url = f"{base_url}/next/rest/si/static/submitActivityTask"
    body = get_submit_body()
    submit_data = _post_json_with_retry(
        session,
        submit_url,
        json=body,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="submitActivityTask",
    )

    if not submit_data.get("submittedSuccess"):
        has_error, warning_only = _has_submit_errors(submit_data)
        if has_error:
            raise RuntimeError(
                f"submitActivityTask failed: {_submit_errors_message(submit_data)}"
            )
        if warning_only:
            body = get_submit_body()
            body["stopOnWarning"] = False
            submit_data = _post_json_with_retry(
                session,
                submit_url,
                json=body,
                max_attempts=max_retries,
                retry_delay=retry_delay,
                report_label=report_label,
                step_name="submitActivityTask (warnings retry)",
            )
            if not submit_data.get("submittedSuccess"):
                raise RuntimeError(
                    f"submitActivityTask failed after retry (warnings): {_submit_errors_message(submit_data)}"
                )
        else:
            raise RuntimeError(
                f"submitActivityTask did not report success: {_submit_errors_message(submit_data)}"
            )

    task_id = extract_task_id(submit_data)
    if not task_id:
        raise RuntimeError("Could not get taskID from submit response.")
    if report_label:
        print(f"[{report_label}] Task submitted: {task_id}")
    else:
        print(f"Task submitted: {task_id}")

    if post_submit_hook:
        post_submit_hook(session)

    coid = body.get("_userContext_vg_coid", "03")
    divid = body.get("_userContext_vg_divid", "1")
    dftdpt = body.get("_userContext_vg_dftdpt", "570")

    poll_url = f"{base_url}/next/rest/si/presenter/autoPollResponse"
    poll_body = {
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": activity_tab_id,
        "ctrlProp": [
            {"name": "ttActivityTask.taskID", "prop": "SCREENVALUE", "value": task_id}
        ],
        "uiType": "ISC",
    }
    for i in range(max_polls):
        time.sleep(poll_interval)
        poll_data = _post_json_with_retry(
            session,
            poll_url,
            json=poll_body,
            max_attempts=max_retries,
            retry_delay=retry_delay,
            report_label=report_label,
            step_name="poll",
        )
        if is_poll_done(poll_data):
            msg = "Report generation complete."
            if report_label:
                msg = f"[{report_label}] {msg}"
            print(msg)
            break
        msg = f"  Poll {i + 1}: still generating..."
        if report_label:
            msg = f"  [{report_label}] Poll {i + 1}: still generating..."
        print(msg)
    else:
        raise RuntimeError("Timed out waiting for report.")

    load_url = f"{base_url}/next/rest/si/static/loadData"
    load_body = {
        "taskID": task_id,
        "ctrlProp": [{"name": "dummy", "prop": "LOADDATA", "value": "dummy"}],
        "parentActivity": None,
        "historyID": "self,dummy,dummy",
        "tabID": "self",
        "activityType": "dummy",
        "fluidService": "dummy",
        "uiType": "ISC",
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": activity_tab_id,
        "loadMode": "EDIT",
        "loadRowid": "dummy",
    }
    load_data = _post_json_with_retry(
        session,
        load_url,
        json=load_body,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="loadData",
    )

    response_url = get_response_url_from_load_data(load_data)
    if not response_url:
        raise RuntimeError("Could not get responseUrl from loadData.")

    if not response_url.startswith("http"):
        response_url = f"{base_url}/next/{response_url.lstrip('/')}"
    if report_label:
        print(f"[{report_label}] Download URL: {response_url}")
    else:
        print(f"Download URL: {response_url}")

    content = _get_content_with_retry(
        session,
        response_url,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="download",
    )
    if output_path is None:
        return content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)
    if report_label:
        print(f"[{report_label}] Saved: {output_path}")
    else:
        print(f"Saved: {output_path}")
    return output_path
