"""
Supplier part enquiry: search by part number (getResults), then load full part data (loadData).
Uses Revolution Next REST API: IM.INQ.SupplierPartDash (search) and IM.INQ.SupplierPart (load).
"""

from typing import Any

import requests

GET_RESULTS_SERVICE = "Revolution.Activity.IM.INQ.SupplierPartDashPR"
LOAD_DATA_SERVICE = "Revolution.Activity.IM.INQ.SupplierPartPR"
ACTIVITY_TAB_ID = "Ne2c02942_66b0_42b3_bb47_a5d466a3f3b4"
ACTIVITY_TAB_ID_OVERVIEW = f"{ACTIVITY_TAB_ID}_Overview"


def _get_results_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/next/rest/si/static/getResults"


def _load_data_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/next/rest/si/static/loadData"


def search_supplier_parts(
    session: requests.Session,
    base_url: str,
    prtid: str,
    *,
    coid: str = "03",
    divid: str = "1",
    dftdpt: str = "570",
    batch_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Search supplier parts by part number (prtid).
    Returns a list of result rows, each with x_rowid, supid, supprt, prtdsc, supprc, spnam, etc.
    Use x_rowid from the desired row in load_supplier_part() to load full part data.
    """
    url = _get_results_url(base_url)
    body = {
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": ACTIVITY_TAB_ID,
        "batchSize": batch_size,
        "prtid": prtid,
        "uiType": "ISC",
    }
    session.headers["x-service-object"] = GET_RESULTS_SERVICE
    r = session.post(url, json=body)
    r.raise_for_status()
    data = r.json()
    for ds in data.get("dataSets", []):
        if ds.get("name") != "dsResult":
            continue
        inner = ds.get("dataSet", {}).get("dsResult", {})
        rows = inner.get("tt_results", [])
        return list(rows)
    return []


def load_supplier_part(
    session: requests.Session,
    base_url: str,
    row_id: str,
    *,
    coid: str = "03",
    divid: str = "1",
    dftdpt: str = "570",
) -> dict[str, Any] | None:
    """
    Load full supplier part data for a row returned by search_supplier_parts.
    row_id is the x_rowid value (e.g. "AAAAABXxHII=") for the supplier part row.
    Returns the single tt_part row, or None if not found.
    """
    url = _load_data_url(base_url)
    body = {
        "ctrlProp": [{"name": "dummy", "prop": "LOADDATA", "value": row_id}],
        "parentActivity": "IM.INQ.SupplierPartDash",
        "uiType": "ISC",
        "_userContext_vg_coid": coid,
        "_userContext_vg_divid": divid,
        "_userContext_vg_dftdpt": dftdpt,
        "activityTabId": ACTIVITY_TAB_ID_OVERVIEW,
        "loadMode": "VIEW",
        "loadRowid": row_id,
    }
    session.headers["x-service-object"] = LOAD_DATA_SERVICE
    r = session.post(url, json=body)
    r.raise_for_status()
    data = r.json()
    for ds in data.get("dataSets", []):
        if ds.get("name") != "dsPart":
            continue
        inner = ds.get("dataSet", {}).get("dsPart", {})
        rows = inner.get("tt_part", [])
        return rows[0] if rows else None
    return None


if __name__ == "__main__":
    """Example: search part PZQ6160670, then load the row for supplier 7001 (Toyota)."""
    from revnext.common import get_or_create_session
    from revnext.config import RevNextConfig

    config = RevNextConfig.from_env()
    session = get_or_create_session(config, GET_RESULTS_SERVICE)
    base_url = config.base_url

    prtid = "PZQ6160670"
    print(f"Searching supplier parts for {prtid}...")
    rows = search_supplier_parts(session, base_url, prtid)
    if not rows:
        print("No supplier parts found.")
        raise SystemExit(1)
    for r in rows:
        print(
            f"  supid={r.get('supid')} spnam={r.get('spnam')} supprc={r.get('supprc')} x_rowid={r.get('x_rowid')}"
        )

    # Load first row (or pick by supid, e.g. 7001 for Toyota)
    supid_want = "7001"
    row = next((r for r in rows if r.get("supid") == supid_want), rows[0])
    row_id = row["x_rowid"]
    print(f"\nLoading full part for supid={row.get('supid')} (x_rowid={row_id})...")
    part = load_supplier_part(session, base_url, row_id)
    if part:
        print(
            f"  prtid={part.get('prtid')} prtdsc={part.get('prtdsc')} supprc={part.get('supprc')} spnam={part.get('spnam')}"
        )
    else:
        print("  Load returned no data.")
