"""
SmartCenter notification helpers for Revolution Next.

Report downloads create "ready to download" notifications under
Revolution.Activity.XA.DLY.NextNotificationPR. Automated syncs never opened
those in the UI, so the unread backlog grew without bound.

The browser "close" control only hides the popup; clearing a notification is
done by acknowledging the matching row (x_rowid) via loadData. Type "r"
(report) rows are matched by taskID in their download url.
"""

from __future__ import annotations

import requests

from revnext.logger import get_logger

logger = get_logger(__name__)

NOTIFICATION_SERVICE = "Revolution.Activity.XA.DLY.NextNotificationPR"
_GET_RESULTS_URL = "/next/rest/si/static/getResults"
_LOAD_DATA_URL = "/next/rest/si/static/loadData"


def _notifications_from_response(payload: dict) -> list[dict]:
    """Extract notification rows from a NextNotificationPR getResults payload."""
    for ds in payload.get("dataSets") or []:
        data_set = ds.get("dataSet") or {}
        response_data = data_set.get("responseData") or {}
        rows = response_data.get("notification")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    return []


def list_notifications(
    session: requests.Session,
    base_url: str,
    *,
    batch_size: int = 50,
) -> list[dict]:
    """
    Return current SmartCenter notification rows (may be truncated by batchSize).

    Restores the previous x-service-object header afterwards.
    """
    url = f"{base_url.rstrip('/')}{_GET_RESULTS_URL}"
    previous = session.headers.get("x-service-object")
    session.headers["x-service-object"] = NOTIFICATION_SERVICE
    try:
        r = session.post(
            url,
            json={
                "DEVICETYPE": "PC",
                "batchSize": batch_size,
                "uiType": "SmartCenter",
            },
        )
        r.raise_for_status()
        return _notifications_from_response(r.json())
    finally:
        if previous is None:
            session.headers.pop("x-service-object", None)
        else:
            session.headers["x-service-object"] = previous


def _acknowledge_notification(
    session: requests.Session,
    base_url: str,
    row: dict,
) -> None:
    """Mark a single notification row as handled via loadData on its x_rowid."""
    row_id = row.get("x_rowid")
    if not row_id:
        raise ValueError("notification row missing x_rowid")
    url = f"{base_url.rstrip('/')}{_LOAD_DATA_URL}"
    keep_keys = (
        "seqno",
        "priority",
        "type",
        "subject",
        "url",
        "x_rowid",
        "fldid",
    )
    notification_row = {
        key: row.get(key) for key in keep_keys if row.get(key) is not None
    }
    notification_row["read"] = True
    body = {
        "DEVICETYPE": "PC",
        "uiType": "SmartCenter",
        "loadMode": "EDIT",
        "loadRowid": row_id,
        "ctrlProp": [
            {"name": "notification.x_rowid", "prop": "SCREENVALUE", "value": row_id},
            {"name": "notification.read", "prop": "SCREENVALUE", "value": "true"},
        ],
        "dataSets": [
            {
                "name": "responseData",
                "dataSet": {
                    "responseData": {"notification": [notification_row]},
                },
            }
        ],
    }
    r = session.post(url, json=body)
    r.raise_for_status()


def dismiss_notifications_for_task(
    session: requests.Session,
    base_url: str,
    task_id: str,
    *,
    batch_size: int = 200,
) -> int:
    """
    Dismiss SmartCenter notifications whose url contains the given taskID.

    Returns how many rows were acknowledged. Failures are logged and skipped so
    a dismiss problem never fails a successful report download.
    """
    if not task_id:
        return 0
    previous = session.headers.get("x-service-object")
    session.headers["x-service-object"] = NOTIFICATION_SERVICE
    dismissed = 0
    try:
        rows = list_notifications(session, base_url, batch_size=batch_size)
        matches = [
            row
            for row in rows
            if task_id in str(row.get("url") or "")
            or task_id in str(row.get("subject") or "")
        ]
        if not matches:
            logger.debug(
                "No SmartCenter notifications matched taskID %s (listed %d).",
                task_id,
                len(rows),
            )
            return 0
        for row in matches:
            try:
                _acknowledge_notification(session, base_url, row)
                dismissed += 1
            except (requests.RequestException, ValueError, TypeError) as e:
                logger.warning(
                    "Could not dismiss notification x_rowid=%s for task %s: %s",
                    row.get("x_rowid"),
                    task_id,
                    e,
                )
        if dismissed:
            logger.info(
                "Dismissed %d SmartCenter notification(s) for task %s.",
                dismissed,
                task_id,
            )
        return dismissed
    except (requests.RequestException, ValueError, TypeError) as e:
        logger.warning(
            "Could not list/dismiss SmartCenter notifications for task %s: %s",
            task_id,
            e,
        )
        return 0
    finally:
        if previous is None:
            session.headers.pop("x-service-object", None)
        else:
            session.headers["x-service-object"] = previous
