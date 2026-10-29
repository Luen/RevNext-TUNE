"""
Compatibility re-exports for Revolution Next shared helpers.

Prefer importing from ``revnext.http`` (sessions, retries, JSON) or
``revnext.report_flow`` (submit/poll/loadData/download) directly.
"""

from revnext.http import (
    MIN_JSON_BODY_LENGTH,
    ReportDownloadError,
    SessionSlot,
    TimeoutSession,
    _body_snippet,
    _common_headers,
    _error_suggests_relogin,
    _get_content_with_retry,
    _looks_like_html,
    _parse_json_response,
    _post_json_with_retry,
    _response_error_context,
    new_session,
)
from revnext.report_flow import (
    REVNEXT_TIMEZONE,
    _has_submit_errors,
    _run_report_flow_once,
    _submit_errors_message,
    extract_task_id,
    get_or_create_session,
    get_response_url_from_load_data,
    is_poll_done,
    new_activity_tab_id,
    open_scheduler_activity,
    revnext_now,
    revnext_offset_text,
    run_report_flow,
)

__all__ = [
    "MIN_JSON_BODY_LENGTH",
    "REVNEXT_TIMEZONE",
    "ReportDownloadError",
    "SessionSlot",
    "TimeoutSession",
    "_body_snippet",
    "_common_headers",
    "_error_suggests_relogin",
    "_get_content_with_retry",
    "_has_submit_errors",
    "_looks_like_html",
    "_parse_json_response",
    "_post_json_with_retry",
    "_response_error_context",
    "_run_report_flow_once",
    "_submit_errors_message",
    "extract_task_id",
    "get_or_create_session",
    "get_response_url_from_load_data",
    "is_poll_done",
    "new_activity_tab_id",
    "new_session",
    "open_scheduler_activity",
    "revnext_now",
    "revnext_offset_text",
    "run_report_flow",
]
