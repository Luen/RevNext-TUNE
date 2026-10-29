"""
SmartCenter notification helpers for Revolution Next.

Report downloads create "ready to download" notifications under
Revolution.Activity.XA.DLY.NextNotificationPR. Automated syncs never opened
those in the UI, so the unread backlog grew without bound.

Type "r" (report) rows are matched by taskID in their download url. Dismiss
tries loadData acknowledge first, then a delete-style dataSets payload, then
re-lists to confirm the row is gone from the batch.
"""

from __future__ import annotations

import argparse
import sys

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


def _header_from_response(payload: dict) -> dict | None:
    for ds in payload.get("dataSets") or []:
        data_set = ds.get("dataSet") or {}
        response_data = data_set.get("responseData") or {}
        header = response_data.get("header")
        if isinstance(header, list) and header:
            row = header[0]
            if isinstance(row, dict):
                return row
    return None


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
        payload = r.json()
        header = _header_from_response(payload)
        if header:
            logger.debug(
                "SmartCenter notifications header count=%s unread=%s",
                header.get("count"),
                header.get("unread"),
            )
        return _notifications_from_response(payload)
    finally:
        if previous is None:
            session.headers.pop("x-service-object", None)
        else:
            session.headers["x-service-object"] = previous


def _notification_row_payload(row: dict, *, deleted: bool = False) -> dict:
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
    if deleted:
        notification_row["_operation"] = "delete"
    else:
        notification_row["read"] = True
    return notification_row


def _post_notification_load(
    session: requests.Session,
    base_url: str,
    row: dict,
    *,
    deleted: bool,
) -> None:
    row_id = row.get("x_rowid")
    if not row_id:
        raise ValueError("notification row missing x_rowid")
    url = f"{base_url.rstrip('/')}{_LOAD_DATA_URL}"
    body = {
        "DEVICETYPE": "PC",
        "uiType": "SmartCenter",
        "loadMode": "EDIT",
        "loadRowid": row_id,
        "ctrlProp": [
            {"name": "notification.x_rowid", "prop": "SCREENVALUE", "value": row_id},
            {
                "name": "notification.read",
                "prop": "SCREENVALUE",
                "value": "true" if not deleted else "false",
            },
        ],
        "dataSets": [
            {
                "name": "responseData",
                "dataSet": {
                    "responseData": {
                        "notification": [
                            _notification_row_payload(row, deleted=deleted)
                        ]
                    },
                },
                "trackingChanges": deleted,
            }
        ],
    }
    r = session.post(url, json=body)
    r.raise_for_status()


def _row_still_listed(
    session: requests.Session,
    base_url: str,
    row_id: str,
    *,
    batch_size: int,
) -> bool:
    rows = list_notifications(session, base_url, batch_size=batch_size)
    return any(str(r.get("x_rowid")) == str(row_id) for r in rows)


def _acknowledge_notification(
    session: requests.Session,
    base_url: str,
    row: dict,
    *,
    batch_size: int = 200,
) -> bool:
    """
    Dismiss one notification. Returns True if the row is no longer in a fresh list.

    Tries read/ack loadData, then a delete-style payload if the row remains listed.
    """
    row_id = row.get("x_rowid")
    if not row_id:
        raise ValueError("notification row missing x_rowid")

    _post_notification_load(session, base_url, row, deleted=False)
    if not _row_still_listed(session, base_url, row_id, batch_size=batch_size):
        return True

    logger.info(
        "Notification x_rowid=%s still listed after read ack; trying delete payload.",
        row_id,
    )
    _post_notification_load(session, base_url, row, deleted=True)
    if not _row_still_listed(session, base_url, row_id, batch_size=batch_size):
        return True

    logger.warning(
        "Notification x_rowid=%s still listed after ack and delete attempts "
        "(type=%s subject=%r).",
        row_id,
        row.get("type"),
        row.get("subject"),
    )
    return False


def dismiss_notifications_for_task(
    session: requests.Session,
    base_url: str,
    task_id: str,
    *,
    batch_size: int = 200,
) -> int:
    """
    Dismiss SmartCenter notifications whose url contains the given taskID.

    Returns how many rows were confirmed removed from a follow-up list. Failures
    are logged and skipped so a dismiss problem never fails a successful report
    download.
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
                if _acknowledge_notification(
                    session, base_url, row, batch_size=batch_size
                ):
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


def dismiss_report_notifications(
    session: requests.Session,
    base_url: str,
    *,
    subject_contains: str | None = None,
    limit: int | None = None,
    batch_size: int = 500,
    dry_run: bool = False,
) -> int:
    """
    Dismiss type-r (report) notifications, optionally filtered by subject substring.

    Intended for ops backlog cleanup. Does not wipe unrelated notification types.
    Returns how many rows were confirmed dismissed (0 when dry_run).
    """
    previous = session.headers.get("x-service-object")
    session.headers["x-service-object"] = NOTIFICATION_SERVICE
    dismissed = 0
    try:
        rows = list_notifications(session, base_url, batch_size=batch_size)
        matches = [row for row in rows if str(row.get("type") or "") == "r"]
        if subject_contains:
            needle = subject_contains.lower()
            matches = [
                row
                for row in matches
                if needle in str(row.get("subject") or "").lower()
            ]
        if limit is not None:
            matches = matches[: max(0, limit)]
        logger.info(
            "Found %d type-r notification(s) to dismiss (dry_run=%s).",
            len(matches),
            dry_run,
        )
        if dry_run:
            for row in matches[:20]:
                logger.info(
                    "dry-run: %s x_rowid=%s subject=%r",
                    row.get("type"),
                    row.get("x_rowid"),
                    row.get("subject"),
                )
            if len(matches) > 20:
                logger.info("dry-run: ... and %d more", len(matches) - 20)
            return 0
        for row in matches:
            try:
                if _acknowledge_notification(
                    session, base_url, row, batch_size=batch_size
                ):
                    dismissed += 1
            except (requests.RequestException, ValueError, TypeError) as e:
                logger.warning(
                    "Could not dismiss notification x_rowid=%s: %s",
                    row.get("x_rowid"),
                    e,
                )
        logger.info("Dismissed %d type-r notification(s).", dismissed)
        return dismissed
    finally:
        if previous is None:
            session.headers.pop("x-service-object", None)
        else:
            session.headers["x-service-object"] = previous


def _cli(argv: list[str] | None = None) -> int:
    from revnext.config import RevNextConfig
    from revnext.session import get_or_create_session

    parser = argparse.ArgumentParser(
        description=(
            "List or dismiss RevNext SmartCenter report (type-r) notifications. "
            "Does not wipe non-report notifications."
        )
    )
    parser.add_argument(
        "--subject-contains",
        default="ready to download",
        help="Only type-r rows whose subject contains this text (default: ready to download)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max rows to dismiss (default: all matches in the batch)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="SmartCenter getResults batchSize (default: 500)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matches only; do not dismiss",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Print header counts and sample rows, then exit",
    )
    args = parser.parse_args(argv)

    config = RevNextConfig.from_env()
    session = get_or_create_session(config, NOTIFICATION_SERVICE)
    if args.list_only:
        rows = list_notifications(session, config.base_url, batch_size=args.batch_size)
        report_rows = [r for r in rows if str(r.get("type") or "") == "r"]
        print(f"listed={len(rows)} type_r={len(report_rows)}")
        for row in report_rows[:30]:
            print(
                f"  {row.get('x_rowid')} {row.get('subject')!r} url={row.get('url')!r}"
            )
        return 0

    dismiss_report_notifications(
        session,
        config.base_url,
        subject_contains=args.subject_contains or None,
        limit=args.limit,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
