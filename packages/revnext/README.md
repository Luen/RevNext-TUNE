# revnext

Download Revolution Next (*.revolutionnext.com.au) reports (Parts Price List, Parts by Bin Location) via REST API. Uses **auto-login** and saves the session to disk so the next run reuses it; if the session is invalid, it logs in again automatically.

- **Install:** `pip install revnext`  
- **Editable (from repo root):** `pip install -e ./packages/revnext`

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

Use the params class to set company, division, department, filters (franchise, bin, stock type, etc.) when you need non-defaults. Pass an instance as `report_params=...`; if omitted, defaults are used.

## Parts enquiries – supplier part

Search for supplier parts by part number and load full part data (e.g. dimensions, weight, price) from the **Supplier Part** enquiry. Import from `revnext.parts` or `revnext.parts.enquiries.supplier_part`:

```python
from revnext.common import get_or_create_session
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

See the [main repo README](https://github.com/Luen/RevNext-TUNE) for the monorepo layout.
