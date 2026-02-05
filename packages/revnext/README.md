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
