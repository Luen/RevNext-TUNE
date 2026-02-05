"""
Shared utilities for Revolution Next (*.revolutionnext.com.au) report downloads.
Session creation (auto-login with persistence) and generic submit → poll → loadData → download flow.
"""

import time
from pathlib import Path
from typing import Callable

import requests

from revnext.config import RevNextConfig


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


def get_or_create_session(config: RevNextConfig, service_object: str) -> requests.Session:
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
) -> Path | bytes:
    """
    Submit report task, poll until ready, loadData for download URL, then download CSV.
    On submit: if response has ERROR, raises; if only WARNING and not success, retries once with stopOnWarning=False.
    Optionally call post_submit_hook(session) after submit (e.g. onChoose_btn_closesubmit).
    If output_path is set: save content to file and return the Path.
    If output_path is None: return the report content as bytes (caller can save or load into pandas).
    """
    submit_url = f"{base_url}/next/rest/si/static/submitActivityTask"
    body = get_submit_body()
    r = session.post(submit_url, json=body)
    r.raise_for_status()
    submit_data = r.json()

    if not submit_data.get("submittedSuccess"):
        has_error, warning_only = _has_submit_errors(submit_data)
        if has_error:
            raise RuntimeError(f"submitActivityTask failed: {_submit_errors_message(submit_data)}")
        if warning_only:
            body = get_submit_body()
            body["stopOnWarning"] = False
            r = session.post(submit_url, json=body)
            r.raise_for_status()
            submit_data = r.json()
            if not submit_data.get("submittedSuccess"):
                raise RuntimeError(
                    f"submitActivityTask failed after retry (warnings): {_submit_errors_message(submit_data)}"
                )
        else:
            raise RuntimeError(f"submitActivityTask did not report success: {_submit_errors_message(submit_data)}")

    task_id = extract_task_id(submit_data)
    if not task_id:
        raise RuntimeError("Could not get taskID from submit response.")
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
        r = session.post(poll_url, json=poll_body)
        r.raise_for_status()
        poll_data = r.json()
        if is_poll_done(poll_data):
            print("Report generation complete.")
            break
        print(f"  Poll {i + 1}: still generating...")
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
    r = session.post(load_url, json=load_body)
    r.raise_for_status()
    load_data = r.json()

    response_url = get_response_url_from_load_data(load_data)
    if not response_url:
        raise RuntimeError("Could not get responseUrl from loadData.")

    if not response_url.startswith("http"):
        response_url = f"{base_url}/next/{response_url.lstrip('/')}"
    print(f"Download URL: {response_url}")

    r = session.get(response_url)
    r.raise_for_status()
    if output_path is None:
        return r.content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(r.content)
    print(f"Saved: {output_path}")
    return output_path
