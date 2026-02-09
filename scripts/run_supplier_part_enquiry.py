"""
Test the supplier-part enquiry: search for part PZQ6160670, load full part data, print dimensions.
Run from repo root with revnext installed: pip install -e packages/revnext

  python scripts/run_supplier_part_enquiry.py

Requires REVNEXT_URL, REVNEXT_USERNAME, REVNEXT_PASSWORD in env (or .env).
"""

import sys

from revnext.common import get_or_create_session
from revnext.config import RevNextConfig
from revnext.parts.enquiries.supplier_part import (
    GET_RESULTS_SERVICE,
    load_supplier_part,
    search_supplier_parts,
)


def main() -> bool:
    try:
        config = RevNextConfig.from_env()
        config.validate()
    except ValueError as e:
        print(f"Config invalid: {e}", file=sys.stderr)
        return False

    session = get_or_create_session(config, GET_RESULTS_SERVICE)
    base_url = config.base_url

    prtid = "PZQ6160670"
    print(f"Searching supplier parts for {prtid}...")
    rows = search_supplier_parts(session, base_url, prtid)
    if not rows:
        print("No supplier parts found.")
        return False

    # Load part from Toyota (supid 7001)
    row = next((r for r in rows if r.get("supid") == "7001"), None)
    if not row:
        print("Supplier 7001 (Toyota) not found in results.")
        return False
    row_id = row["x_rowid"]
    print(f"Loading part from supplier {row.get('supid')} ({row.get('spnam')})...")
    part = load_supplier_part(session, base_url, row_id)
    if not part:
        print("Load returned no data.")
        return False

    # Part details: length, width, height, volume, weight
    length = part.get("prtlen")
    length_unit = part.get("untlen") or ""
    width = part.get("prtwdt")
    width_unit = part.get("untwdt") or ""
    height = part.get("prthgt")
    height_unit = part.get("unthgt") or ""
    volume = part.get("prtvol")
    volume_unit = part.get("untvol") or ""
    weight = part.get("prtwgt")
    weight_unit = part.get("untwgt") or ""

    print()
    print("Part details")
    print("------------")
    print(f"  Part number:     {part.get('prtid')}")
    print(f"  Description:     {part.get('prtdsc')}")
    print(f"  Supplier part:   {part.get('supprt')}")
    print(f"  Supplier:        {part.get('spnam')} ({part.get('supid')})")
    print(f"  Length:          {length} {length_unit}".strip())
    print(f"  Width:           {width} {width_unit}".strip())
    print(f"  Height:          {height} {height_unit}".strip())
    print(f"  Volume:          {volume} {volume_unit}".strip())
    print(f"  Weight:          {weight} {weight_unit}".strip())
    print()
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
