"""
Part general enquiry: search by part number/description (getResults), then load only the tab(s) needed (loadData).
Uses Revolution Next REST API: IM.INQ.PartDash (search) and tab-specific services (load).
Callers should request only the tabs they need (e.g. part_suppliers only).
"""

from typing import Any

import requests

GET_RESULTS_SERVICE = "Revolution.Activity.IM.INQ.PartDashPR"
ACTIVITY_TAB_ID = "Nc262c3a4_e630_4a99_8cd0_70cc9dd9f149"

# Tab key -> (service name, dataset name) for loadData
TAB_REGISTRY: dict[str, tuple[str, str]] = {
    "header": ("Revolution.Activity.IM.INQ.PartHeaderPR", "dsDetails"),
    "details": ("Revolution.Activity.IM.INQ.PartDetailsPR", "dsDetails"),
    "activity": ("Revolution.Activity.IM.INQ.PartActivityPR", "dsDetails"),
    "other": ("Revolution.Activity.IM.INQ.PartOtherInfoPR", "dsOther"),
    "stock": ("Revolution.Activity.IM.INQ.PartStockPR", "dsStock"),
    "movement": ("Revolution.Activity.IM.INQ.PartMovementPR", "dsMovement"),
    "history": ("Revolution.Activity.IM.INQ.PartHistoryPR", "dsHistory"),
    "on_order": ("Revolution.Activity.IM.INQ.PartOnOrderPR", "dsOnOrder"),
    "rip": ("Revolution.Activity.IM.INQ.PartReceiptInProgressPR", "dsRip"),
    "stock_in_transit": (
        "Revolution.Activity.IM.INQ.PartStockInTransitPR",
        "dsInTransit",
    ),
    "service_in_progress": (
        "Revolution.Activity.IM.INQ.PartServiceInProgressPR",
        "dsServiceInProgress",
    ),
    "back_order": ("Revolution.Activity.IM.INQ.PartBackorderPR", "dsBackorder"),
    "part_suppliers": ("Revolution.Activity.IM.INQ.PartSuppliersPR", "dsPartSuppliers"),
    "modification_log": (
        "Revolution.Activity.IM.INQ.PartsModificationLogPR",
        "dsModificationLog",
    ),
}


def _get_results_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/next/rest/si/static/getResults"


def _load_data_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/next/rest/si/static/loadData"


def search_part_general(
    session: requests.Session,
    base_url: str,
    search_str: str,
    *,
    frnid: str | None = None,
    binid: str | None = None,
    stkflg: bool = False,
    coid: str = "03",
    divid: str = "1",
    dftdpt: str = "570",
    batch_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Search parts by part number or description (search_str).
    Returns a list of result rows, each with x_rowid and identifying fields
    (frnid, prtid, prtdsc, binid, supid, stktot, prcext, etc.) so the user/caller
    can see options and select the correct part. Each row's x_rowid is valid for load_part_tab.
    When frnid/binid are omitted or empty, the API may return multiple rows (e.g. one per franchise).
    """
    url = _get_results_url(base_url)
    body: dict[str, Any] = {
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": ACTIVITY_TAB_ID,
        "batchSize": batch_size,
        "search_str": search_str,
        "stkflg": stkflg,
        "x_rowid": "",
        "uiType": "ISC",
    }
    if frnid is not None and frnid != "":
        body["frnid"] = frnid
    if binid is not None and binid != "":
        body["binid"] = binid
    session.headers["x-service-object"] = GET_RESULTS_SERVICE
    r = session.post(url, json=body)
    r.raise_for_status()
    data = r.json()
    for ds in data.get("dataSets", []):
        if ds.get("name") != "dsResults":
            continue
        inner = ds.get("dataSet", {}).get("dsResults", {})
        rows = inner.get("tt_results", [])
        return list(rows)
    return []


def load_part_tab(
    session: requests.Session,
    base_url: str,
    row_id: str,
    tab: str,
    *,
    coid: str = "03",
    divid: str = "1",
    dftdpt: str = "570",
) -> dict[str, Any] | None:
    """
    Load data for a single tab for a part row returned by search_part_general.
    row_id is the x_rowid value for the part row. tab is one of the tab keys
    (e.g. "part_suppliers", "details", "header"). Returns the dataset contents
    (e.g. {"tt_supprt_list": [...], "tt_supprt_dtls": [...]}) or None if not found.
    Callers should request only the tabs they need.
    """
    if tab not in TAB_REGISTRY:
        return None
    service, dataset_name = TAB_REGISTRY[tab]
    url = _load_data_url(base_url)
    activity_tab_id = f"{ACTIVITY_TAB_ID}_{tab}"
    body = {
        "ctrlProp": [{"name": "dummy", "prop": "LOADDATA", "value": row_id}],
        "parentActivity": "IM.INQ.PartDash",
        "uiType": "ISC",
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": activity_tab_id,
        "loadMode": "VIEW",
        "loadRowid": row_id,
    }
    session.headers["x-service-object"] = service
    r = session.post(url, json=body)
    r.raise_for_status()
    data = r.json()
    for ds in data.get("dataSets", []):
        if ds.get("name") != dataset_name:
            continue
        inner = ds.get("dataSet", {}).get(dataset_name, {})
        return dict(inner) if isinstance(inner, dict) else {}
    return None


def load_part_tabs(
    session: requests.Session,
    base_url: str,
    row_id: str,
    tabs: list[str],
    *,
    coid: str = "03",
    divid: str = "1",
    dftdpt: str = "570",
) -> dict[str, dict[str, Any] | None]:
    """
    Load multiple tabs for a part row. tabs is an iterable of tab keys.
    Returns a dict mapping each tab key to its dataset contents (or None).
    Only the requested tabs are requested from the server.
    """
    result: dict[str, dict[str, Any] | None] = {}
    for t in tabs:
        result[t] = load_part_tab(
            session, base_url, row_id, t, coid=coid, divid=divid, dftdpt=dftdpt
        )
    return result


if __name__ == "__main__":
    """Example: search part, show results for user to select, then load part_suppliers for chosen row."""
    from revnext.common import get_or_create_session
    from revnext.config import RevNextConfig

    config = RevNextConfig.from_env()
    session = get_or_create_session(config, GET_RESULTS_SERVICE)
    base_url = config.base_url

    search_str = "BUTO70171784.5P60WIS"
    print(f"Searching parts for {search_str}...")
    rows = search_part_general(session, base_url, search_str)
    if not rows:
        print("No parts found.")
        raise SystemExit(1)
    for r in rows:
        print(
            f"  frnid={r.get('frnid')} prtid={r.get('prtid')} prtdsc={r.get('prtdsc')} "
            f"binid={r.get('binid')} stktot={r.get('stktot')} x_rowid={r.get('x_rowid')}"
        )

    # Select by frnid (e.g. OL) or take first
    frnid_want = "OL"
    row = next((r for r in rows if r.get("frnid") == frnid_want), rows[0])
    row_id = row["x_rowid"]
    print(
        f"\nLoading part_suppliers for frnid={row.get('frnid')} (x_rowid={row_id})..."
    )
    data = load_part_tab(session, base_url, row_id, "part_suppliers")
    if data:
        supprt_list = data.get("tt_supprt_list", [])
        supprt_dtls = data.get("tt_supprt_dtls", [])
        for s in supprt_list:
            print(
                f"  frnid={s.get('frnid')} supid={s.get('supid')} spnam={s.get('spnam')} "
                f"supprc={s.get('supprc')}"
            )
        if not supprt_list and supprt_dtls:
            for s in supprt_dtls:
                print(
                    f"  frnid={s.get('frnid')} supid={s.get('supid')} spnam={s.get('spnam')} "
                    f"supprc={s.get('supprc')}"
                )
        if not supprt_list and not supprt_dtls:
            print("  (no supplier rows)")
    else:
        print("  Load returned no data.")
