# revnext

Download Revolution Next (*.revolutionnext.com.au) reports (Parts Price List, Parts by Bin Location) via REST API. Uses **auto-login** and saves the session to disk so the next run reuses it; if the session is invalid, it logs in again automatically.
Also supports:

- **parts** → **reports**: Parts Price List and Parts by Bin Location (CSV download via REST API).
- **parts** → **enquiries**: Supplier Part search/load and Part General Enquiry (search by part number/description, load tab data).

- **Install:** `pip install revnext`  
- **Editable (from repo root):** `pip install -e ./packages/revnext`

## Contents

- [Configuration](#configuration-env)
- [Custom logger](#custom-logger)
- [Parts reports](#parts-reports)
  - [Parts by Bin Location](#parts-reports)
  - [Parts Price List](#parts-reports)
- [Parts enquiries](#parts-enquiries)
  - [Supplier part](#supplier-part)
  - [Part general enquiry](#part-general-enquiry)
- [Quick start](#quick-start)
- [Developer reference](#developer-reference)
  - [Package layout](#package-layout)
  - [Public API](#public-api)
  - [Report parameters](#report-parameters)
  - [Report flow options](#report-flow-options)
  - [Enquiry session and services](#enquiry-session-and-services)

## Configuration (.env)

Put your base URL, username, and password in a `.env` file (e.g. in the project root or cwd). Optional: use `python-dotenv` so `RevNextConfig.from_env()` loads it.

| Variable | Required | Description |
|----------|----------|-------------|
| `REVNEXT_URL` | Yes | Full base URL (e.g. `https://yourtenant.revolutionnext.com.au`) |
| `REVNEXT_USERNAME` | Yes | RevNext login User ID |
| `REVNEXT_PASSWORD` | Yes | RevNext login Password |
| `REVNEXT_SESSION_PATH` | No | Where to save/load session cookies (default: `.revnext-session.json` in cwd) |

Example `.env`:

```env
REVNEXT_URL=https://yourtenant.revolutionnext.com.au
REVNEXT_USERNAME=your_user_id
REVNEXT_PASSWORD=your_password
```

The first run logs in via the web form (CSRF + `j_spring_security_check`) and saves the session to `REVNEXT_SESSION_PATH` or `.revnext-session.json`. Later runs load that file, check that the session is still valid, and only re-login if it has expired.

## Custom logger

You can inject your own logger so all library log output uses your handler, level, and format. Call `set_logger(my_logger)` **before** using other revnext APIs. Pass `None` to revert to the default.

```python
import logging
from revnext import set_logger, download_parts_by_bin_report

logger = logging.getLogger("my_app.revnext")
logger.setLevel(logging.DEBUG)
# add handlers, formatters, etc.
set_logger(logger)

# Now all revnext log output goes to your logger
download_parts_by_bin_report(output_path=Path("reports/parts_by_bin.csv"))
```

## Parts reports

Two report types are supported:

| Report | Function | Params class |
|--------|----------|--------------|
| **Parts by Bin Location** | `download_parts_by_bin_report()` | `PartsByBinLocationParams` |
| **Parts Price List** | `download_parts_price_list_report()` | `PartsPriceListParams` |

Use the params class to set company, division, department, filters (franchise, bin, stock type, etc.) when you need non-defaults. Pass an instance as `report_params=...`; if omitted, defaults are used. If `output_path` is omitted, the CSV is written to the current directory as `Parts_By_Bin_Location.csv` or `Parts_Price_List.csv` respectively (or use `return_data=True` to get CSV bytes without writing a file).

## Parts Enquiries

Look up parts via the **Supplier Part** enquiry (search by part number, load full part data) or the **Part General Enquiry** (search by part number/description, load only the tab(s) you need).

### Supplier Part

Search for supplier parts by part number and load full part data (e.g. dimensions, weight, price) from the **Supplier Part** enquiry. Import from `revnext.parts` or `revnext.parts.enquiries.supplier_part`:

```python
from revnext.common import get_or_create_session
from revnext.config import RevNextConfig
from revnext.parts.enquiries.supplier_part import (
    GET_RESULTS_SERVICE,
    load_supplier_part,
    search_supplier_parts,
)

config = RevNextConfig.from_env()
session = get_or_create_session(config, GET_RESULTS_SERVICE)

# Search by part number (e.g. PZQ6160670)
rows = search_supplier_parts(session, config.base_url, "PZQ6160670")
# Each row has x_rowid, supid, supprt, prtdsc, supprc, spnam, etc.

# Load full part for one supplier (e.g. Toyota supid 7001)
row = next(r for r in rows if r.get("supid") == "7001")
part = load_supplier_part(session, config.base_url, row["x_rowid"])
# part has prtid, prtdsc, prtlen, prtwdt, prthgt, prtvol, prtwgt, supprc, etc. (with untlen, untwdt, unthgt, untvol, untwgt for units)
```

Optional parameters (all have defaults): `search_supplier_parts(..., coid="03", divid="1", dftdpt="570", batch_size=50)`; `load_supplier_part(..., coid="03", divid="1", dftdpt="570")`. Use `GET_RESULTS_SERVICE` and `LOAD_DATA_SERVICE` from `revnext.parts.enquiries.supplier_part` when calling `get_or_create_session()`.

### Part General Enquiry

Search parts by part number or description, then load only the tab(s) you need (header, details, part_suppliers, stock, movement, etc.). Import from `revnext.parts.enquiries.part_general_enquiry`:

```python
from revnext.common import get_or_create_session
from revnext.config import RevNextConfig
from revnext.parts.enquiries.part_general_enquiry import (
    GET_RESULTS_SERVICE,
    TAB_REGISTRY,
    load_part_tab,
    load_part_tabs,
    search_part_general,
)

config = RevNextConfig.from_env()
session = get_or_create_session(config, GET_RESULTS_SERVICE)

# Search by part number or description
rows = search_part_general(session, config.base_url, "BUTO70171784.5P60WIS")
# Optional: narrow by franchise/bin
# rows = search_part_general(session, config.base_url, "BUTO70171784", frnid="OL", binid="A1")
# Each row has x_rowid, frnid, prtid, prtdsc, binid, supid, stktot, prcext, etc.

row = rows[0]
row_id = row["x_rowid"]

# Load a single tab (e.g. part_suppliers); request only the tabs you need
data = load_part_tab(session, config.base_url, row_id, "part_suppliers")
# data has tt_supprt_list, tt_supprt_dtls, etc.

# Or load multiple tabs at once
tabs_data = load_part_tabs(session, config.base_url, row_id, ["header", "part_suppliers", "stock"])
# tabs_data["part_suppliers"], tabs_data["header"], tabs_data["stock"]
```

**Available tab keys** (use with `load_part_tab` / `load_part_tabs`): `header`, `details`, `activity`, `other`, `stock`, `movement`, `history`, `on_order`, `rip`, `stock_in_transit`, `service_in_progress`, `back_order`, `part_suppliers`, `modification_log`. See `TAB_REGISTRY` in `part_general_enquiry.py` for the mapping. Optional params: `search_part_general(..., frnid=None, binid=None, stkflg=False, coid="03", divid="1", dftdpt="570", batch_size=50)`; `load_part_tab` / `load_part_tabs(..., coid="03", divid="1", dftdpt="570")`.

## Quick start

```python
from pathlib import Path
from revnext import download_parts_by_bin_report, download_parts_price_list_report

# Config from env (.env or REVNEXT_*)
path1 = download_parts_by_bin_report(
    output_path=Path("C:/Reports/parts_by_bin.csv"),
)
path2 = download_parts_price_list_report(
    output_path=Path("C:/Reports/parts_price_list.csv"),
)
```

### Return data in memory (e.g. for pandas)

Use `return_data=True` to get the CSV content as bytes without saving a file. Load into pandas with `io.BytesIO`:

```python
import io
import pandas as pd
from revnext import download_parts_by_bin_report, download_parts_price_list_report

# Get report as bytes, then load into a DataFrame
csv_bytes = download_parts_by_bin_report(return_data=True)
df = pd.read_csv(io.BytesIO(csv_bytes))

# Or save to file yourself later
# Path("reports/parts_by_bin.csv").write_bytes(csv_bytes)
```

When `return_data=True`, the function returns `bytes`; when `return_data=False` (default), it saves to `output_path` and returns the `Path`.

### Download one report with explicit config

```python
from pathlib import Path
from revnext import RevNextConfig, download_parts_by_bin_report, download_parts_price_list_report

config = RevNextConfig.from_env()  # or RevNextConfig( base_url="...", username="...", password="...", session_path=... )

path1 = download_parts_by_bin_report(
    config=config,
    output_path=Path("C:/Reports/parts_by_bin.csv"),
)
path2 = download_parts_price_list_report(
    config=config,
    output_path=Path("C:/Reports/parts_price_list.csv"),
)
```

### Example: download both reports (implement in your project)

```python
from pathlib import Path
from typing import Optional

from revnext import RevNextConfig, download_parts_by_bin_report, download_parts_price_list_report


def download_all_reports(
    config: Optional[RevNextConfig] = None,
    output_dir: Optional[Path | str] = None,
) -> list[Path]:
    """Run both reports and save CSVs. Returns the list of paths where files were saved."""
    config = config or RevNextConfig.from_env()
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()
    path1 = download_parts_by_bin_report(
        config=config,
        output_path=output_dir / "Parts_By_Bin_Location.csv",
    )
    path2 = download_parts_price_list_report(
        config=config,
        output_path=output_dir / "Parts_Price_List.csv",
    )
    return [path1, path2]
```

### Example: download both reports in parallel

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from revnext import RevNextConfig, download_parts_by_bin_report, download_parts_price_list_report


def download_all_reports_parallel(
    config: Optional[RevNextConfig] = None,
    output_dir: Optional[Path | str] = None,
) -> list[Path]:
    """Run both reports in parallel. Returns the list of paths where files were saved."""
    config = config or RevNextConfig.from_env()
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()
    path1 = output_dir / "Parts_By_Bin_Location.csv"
    path2 = output_dir / "Parts_Price_List.csv"
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(
            download_parts_by_bin_report,
            config=config,
            output_path=path1,
        )
        f2 = executor.submit(
            download_parts_price_list_report,
            config=config,
            output_path=path2,
        )
        return [f1.result(), f2.result()]
```

## Developer reference

### Package layout

| Path | Purpose |
|------|--------|
| `revnext` | Top-level package; exports config, logger, report download functions, report params |
| `revnext.config` | `RevNextConfig`, `get_revnext_base_url_from_env` |
| `revnext.common` | `get_or_create_session`, `run_report_flow`, `ReportDownloadError` |
| `revnext.logger` | `get_logger`, `set_logger` |
| `revnext.parts` | Re-exports reports and supplier part enquiry |
| `revnext.parts.reports` | `download_parts_by_bin_report`, `download_parts_price_list_report`, `PartsByBinLocationParams`, `PartsPriceListParams` |
| `revnext.parts.reports.parts_by_bin_report` | Parts By Bin Location report implementation |
| `revnext.parts.reports.parts_price_list_report` | Parts Price List report implementation |
| `revnext.parts.enquiries` | Re-exports supplier part enquiry only |
| `revnext.parts.enquiries.supplier_part` | Supplier part: `search_supplier_parts`, `load_supplier_part`, `GET_RESULTS_SERVICE`, `LOAD_DATA_SERVICE` |
| `revnext.parts.enquiries.part_general_enquiry` | Part general: `search_part_general`, `load_part_tab`, `load_part_tabs`, `TAB_REGISTRY`, `GET_RESULTS_SERVICE` |

### Public API

- **Config:** `RevNextConfig`, `RevNextConfig.from_env()`, `get_revnext_base_url_from_env`
- **Logging:** `set_logger(logger)`, `get_logger(name)`
- **Session:** `get_or_create_session(config, service_object)` (from `revnext.common`)
- **Reports:** `download_parts_by_bin_report()`, `download_parts_price_list_report()`; params: `PartsByBinLocationParams`, `PartsPriceListParams`
- **Errors:** `ReportDownloadError` (from `revnext.common` or `revnext`)
- **Supplier Part Enquiry:** `search_supplier_parts`, `load_supplier_part` (from `revnext.parts` or `revnext.parts.enquiries.supplier_part`)
- **Part General Enquiry:** `search_part_general`, `load_part_tab`, `load_part_tabs`, `TAB_REGISTRY`, `GET_RESULTS_SERVICE` (from `revnext.parts.enquiries.part_general_enquiry`)

### Report parameters

**PartsByBinLocationParams** (defaults: company/division/department empty; show "Available Stock")  
Company/division/department, from/to department/franchise/bin/movement_code; `show_stock_as`: `"Physical Stock"` or `"Available Stock"`; `print_when_stock_not_zero`, `print_part_when_stock_zero`, `print_part_when_stock_on_order_zero`; bin filters: `no_primary_bin_location`, `no_alternate_bin_location`, `no_primary_but_has_alternate_bin`, `has_both_primary_and_alternate_bin`; `last_sale_before`, `last_receipt_before` (ISO date-time or None); `print_average_cost`.

**PartsPriceListParams** (defaults: company/division/department empty; part_type `"stock"`; price_1 `"L"`, price_2 `"S"`; include_gst True for both)  
Company, division, department; `part_type`: `"stock"` or `"supplier"`; from/to franchise and bin; `price_1` / `price_2`: API codes (e.g. `"L"` List, `"S"` Stock, `"I"`, `"TG"`, `"R"`, `"ST"`); `include_gst_1`, `include_gst_2`. At least one of `price_1` or `price_2` must be set.

Pass a params instance as `report_params=...` to the report function, or override individual fields via keyword arguments.

### Report flow options

Both report functions accept:

- `config`, `output_path`, `base_url`, `report_params` (and report-specific kwargs that override params)
- `max_polls` (default 60), `poll_interval` (default 2 seconds) for waiting for the report task
- `return_data=True` to return CSV bytes instead of writing to a file
- `report_label` for log messages
- `max_retries` (default 3), `retry_delay` (default 5 seconds) for transient API failures

On transient failures (empty/HTML/invalid JSON response), the library retries and raises `ReportDownloadError` after all retries are exhausted.

### Enquiry session and services

Enquiries use the same session as reports: `get_or_create_session(config, service_object)`. Use the correct `service_object` for the first request:

- **Supplier part search:** `GET_RESULTS_SERVICE` from `revnext.parts.enquiries.supplier_part` (e.g. `Revolution.Activity.IM.INQ.SupplierPartDashPR`)
- **Supplier part load:** `LOAD_DATA_SERVICE` from the same module (e.g. `Revolution.Activity.IM.INQ.SupplierPartPR`)
- **Part general search:** `GET_RESULTS_SERVICE` from `revnext.parts.enquiries.part_general_enquiry` (e.g. `Revolution.Activity.IM.INQ.PartDashPR`)

After a session is created for one of these services, the same session can be used for subsequent getResults/loadData calls to the same or related activities.

See the [main repo README](https://github.com/Luen/RevNext-TUNE) for the monorepo layout.
