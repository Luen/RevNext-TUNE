"""
Submit → poll → loadData → download orchestration for Revolution Next reports.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from revnext.config import RevNextConfig
from revnext.http import (
    ReportDownloadError,
    SessionSlot,
    _error_suggests_relogin,
    _get_content_with_retry,
    _post_json_with_retry,
)
from revnext.logger import get_logger

logger = get_logger(__name__)

# Revolution Next timestamps carry the tenant's local offset. Brisbane has no DST, so a
# fixed +10:00 is exact year-round. Previously the code took a naive datetime.now() from
# whatever machine it ran on and labelled it "+10:00" regardless, so a report submitted
# from any other timezone asked the server for the wrong window.
REVNEXT_TIMEZONE = timezone(timedelta(hours=10))


def revnext_now() -> datetime:
    """Current time in the RevNext tenant's timezone."""
    return datetime.now(REVNEXT_TIMEZONE)


def revnext_offset_text(tz: timezone = REVNEXT_TIMEZONE) -> str:
    """The UTC offset as RevNext formats it, e.g. "+10:00"."""
    offset = tz.utcoffset(None) or timedelta(0)
    sign = "-" if offset < timedelta(0) else "+"
    hours, remainder = divmod(int(abs(offset).total_seconds()), 3600)
    return f"{sign}{hours:02d}:{remainder // 60:02d}"


def new_activity_tab_id() -> str:
    """Client-generated Fluid tab id (``N`` + uuid with underscores), matching the browser."""
    return "N" + str(uuid.uuid4()).replace("-", "_")


def open_scheduler_activity(
    session: requests.Session | SessionSlot,
    base_url: str,
    service_object: str,
    *,
    coid: str,
    divid: str,
    dftdpt: str,
    activity_tab_id: str | None = None,
    report_label: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5,
    relogin: Callable[[], requests.Session] | None = None,
) -> str:
    """
    Open a scheduler activity tab via ``loadActivityDef`` then ``loadData``.

    Returns the activity tab id used (generated when ``activity_tab_id`` is None).
    """
    tab_id = activity_tab_id or new_activity_tab_id()
    history_id = f"{tab_id},sched,{service_object}"
    common = {
        "parentActivity": None,
        "historyID": history_id,
        "tabID": tab_id,
        "activityType": "sched",
        "fluidService": service_object,
        "uiType": "ISC",
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
    }
    _post_json_with_retry(
        session,
        f"{base_url}/next/rest/si/static/loadActivityDef",
        json={**common, "activity": tab_id},
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="loadActivityDef",
        relogin=relogin,
    )
    _post_json_with_retry(
        session,
        f"{base_url}/next/rest/si/static/loadData",
        json={
            **common,
            "activityTabId": tab_id,
            "loadMode": "EDIT",
            "loadRowid": "dummy",
        },
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="loadData (open activity)",
        relogin=relogin,
    )
    prefix = f"[{report_label}] " if report_label else ""
    logger.info("%sOpened activity tab %s for %s", prefix, tab_id, service_object)
    return tab_id


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


def _run_report_flow_once(
    session: requests.Session,
    service_object: str,
    activity_tab_id: str | None,
    get_submit_body: Callable[[], dict],
    base_url: str,
    output_path: Path | None = None,
    post_submit_hook: Callable[[requests.Session, str], None] | None = None,
    max_polls: int = 60,
    poll_interval: float = 2,
    report_label: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5,
    dismiss_notifications: bool = True,
    config: RevNextConfig | None = None,
    open_activity: bool = True,
) -> Path | bytes:
    """
    Single attempt: optionally open the activity tab, submit, poll, loadData, download CSV.

    When ``activity_tab_id`` is None a fresh client tab id is generated. When
    ``open_activity`` is True, ``loadActivityDef`` + ``loadData`` run first (browser-like).
    When ``config`` is set, login-page HTML during a step triggers mid-step re-login.
    """
    from revnext.session import force_relogin

    slot = SessionSlot(session)
    relogin: Callable[[], requests.Session] | None = None
    if config is not None:

        def relogin() -> requests.Session:
            return force_relogin(config, service_object)

    prefix = f"[{report_label}] " if report_label else ""
    probe = get_submit_body()
    coid = probe.get("_userContext_vg_coid", "03")
    divid = probe.get("_userContext_vg_divid", "1")
    dftdpt = probe.get("_userContext_vg_dftdpt", "570")
    tab_id = activity_tab_id or new_activity_tab_id()

    if open_activity:
        tab_id = open_scheduler_activity(
            slot,
            base_url,
            service_object,
            coid=coid,
            divid=divid,
            dftdpt=dftdpt,
            activity_tab_id=tab_id,
            report_label=report_label,
            max_retries=max_retries,
            retry_delay=retry_delay,
            relogin=relogin,
        )

    def get_body_with_tab() -> dict:
        body = get_submit_body()
        body["activityTabId"] = tab_id
        return body

    submit_url = f"{base_url}/next/rest/si/static/submitActivityTask"
    body = get_body_with_tab()
    submit_data = _post_json_with_retry(
        slot,
        submit_url,
        json=body,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="submitActivityTask",
        relogin=relogin,
    )

    if not submit_data.get("submittedSuccess"):
        has_error, warning_only = _has_submit_errors(submit_data)
        if has_error:
            raise RuntimeError(
                f"submitActivityTask failed: {_submit_errors_message(submit_data)}"
            )
        if warning_only:
            body = get_body_with_tab()
            body["stopOnWarning"] = False
            submit_data = _post_json_with_retry(
                slot,
                submit_url,
                json=body,
                max_attempts=max_retries,
                retry_delay=retry_delay,
                report_label=report_label,
                step_name="submitActivityTask (warnings retry)",
                relogin=relogin,
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
    logger.info("%sTask submitted: %s", prefix, task_id)

    if post_submit_hook:
        post_submit_hook(slot.session, tab_id)

    poll_url = f"{base_url}/next/rest/si/presenter/autoPollResponse"
    poll_body = {
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": tab_id,
        "ctrlProp": [
            {"name": "ttActivityTask.taskID", "prop": "SCREENVALUE", "value": task_id}
        ],
        "uiType": "ISC",
    }
    for i in range(max_polls):
        time.sleep(poll_interval)
        poll_data = _post_json_with_retry(
            slot,
            poll_url,
            json=poll_body,
            max_attempts=max_retries,
            retry_delay=retry_delay,
            report_label=report_label,
            step_name="poll",
            relogin=relogin,
        )
        if is_poll_done(poll_data):
            logger.info("%sReport generation complete.", prefix)
            break
        logger.info("%sPoll %d: still generating...", prefix, i + 1)
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
        "activityTabId": tab_id,
        "loadMode": "EDIT",
        "loadRowid": "dummy",
    }
    load_data = _post_json_with_retry(
        slot,
        load_url,
        json=load_body,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="loadData",
        relogin=relogin,
    )

    response_url = get_response_url_from_load_data(load_data)
    if not response_url:
        raise RuntimeError("Could not get responseUrl from loadData.")

    if not response_url.startswith("http"):
        response_url = f"{base_url}/next/{response_url.lstrip('/')}"
    logger.info("%sDownload URL: %s", prefix, response_url)

    content = _get_content_with_retry(
        slot,
        response_url,
        max_attempts=max_retries,
        retry_delay=retry_delay,
        report_label=report_label,
        step_name="download",
        relogin=relogin,
    )
    if dismiss_notifications:
        from revnext.notifications import dismiss_notifications_for_task

        dismiss_notifications_for_task(slot.session, base_url, task_id)

    if output_path is None:
        return content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)
    logger.info("%sSaved: %s", prefix, output_path)
    return output_path


def run_report_flow(
    session: requests.Session,
    service_object: str,
    activity_tab_id: str | None,
    get_submit_body: Callable[[], dict],
    base_url: str,
    output_path: Path | None = None,
    post_submit_hook: Callable[[requests.Session, str], None] | None = None,
    max_polls: int = 60,
    poll_interval: float = 2,
    report_label: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5,
    max_report_attempts: int = 2,
    report_retry_delay: float = 30,
    config: RevNextConfig | None = None,
    dismiss_notifications: bool = True,
    open_activity: bool = True,
) -> Path | bytes:
    """
    Submit report task, poll until ready, loadData for download URL, then download CSV.
    Retries the full flow up to max_report_attempts times on ReportDownloadError or RuntimeError.

    When ``activity_tab_id`` is None, a fresh Fluid tab id is generated each attempt.
    When ``open_activity`` is True (default), the activity is opened via loadActivityDef.
    When ``config`` is provided, login HTML triggers mid-step re-login during retries and
    a full-attempt re-login between report attempts.
    """
    from revnext.session import force_relogin

    last_error: BaseException | None = None
    current_session = session
    for attempt in range(1, max_report_attempts + 1):
        try:
            return _run_report_flow_once(
                current_session,
                service_object,
                activity_tab_id,
                get_submit_body,
                base_url,
                output_path=output_path,
                post_submit_hook=post_submit_hook,
                max_polls=max_polls,
                poll_interval=poll_interval,
                report_label=report_label,
                max_retries=max_retries,
                retry_delay=retry_delay,
                dismiss_notifications=dismiss_notifications,
                config=config,
                open_activity=open_activity,
            )
        except (ReportDownloadError, RuntimeError) as e:
            last_error = e
            if attempt < max_report_attempts:
                prefix = f"[{report_label}] " if report_label else ""
                if config is not None and _error_suggests_relogin(e):
                    logger.warning(
                        "%sFull report attempt %d of %d failed with auth/HTML response "
                        "(%s); re-logging in and retrying in %.1fs.",
                        prefix,
                        attempt,
                        max_report_attempts,
                        e,
                        report_retry_delay,
                    )
                    current_session = force_relogin(config, service_object)
                else:
                    logger.warning(
                        "%sFull report attempt %d of %d failed (%s); retrying in %.1fs.",
                        prefix,
                        attempt,
                        max_report_attempts,
                        e,
                        report_retry_delay,
                    )
                time.sleep(report_retry_delay)
            else:
                break
    label_suffix = f" [{report_label}]" if report_label else ""
    if isinstance(last_error, ReportDownloadError):
        raise last_error
    raise ReportDownloadError(
        f"Report download failed after {max_report_attempts} full attempt(s){label_suffix}: {last_error}"
    ) from last_error
