# revnext

Download Revolution Next (*.revolutionnext.com.au) reports (Parts Price List, Parts by Bin Location) via REST API using cookies/session.

Install: `pip install revnext`  
Or from repo root: `pip install -e ./packages/revnext`

## Quick start

You need a cookies file (Chrome export for your RevNext domain). Then call the download functions with your instance URL and download location.

### Download one report with a specific file path

```python
from pathlib import Path
from revnext import download_parts_by_bin_report, download_parts_price_list_report

base_url = "https://yoursite.revolutionnext.com.au"
cookies_path = Path("revnext-cookies.json")

# Parts by Bin Location
path1 = download_parts_by_bin_report(
    base_url=base_url,
    output_path=Path("C:/Reports/parts_by_bin.csv"),
    cookies_path=cookies_path,
)

# Parts Price List
path2 = download_parts_price_list_report(
    base_url=base_url,
    output_path=Path("C:/Reports/parts_price_list.csv"),
    cookies_path=cookies_path,
)
```

### Example: download both reports (implement in your project)

Copy this into your project to run both reports in sequence:

```python
from pathlib import Path
from typing import Optional

from revnext import download_parts_by_bin_report, download_parts_price_list_report


def download_all_reports(
    cookies_path: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    base_url: Optional[str] = None,
) -> list[Path]:
    """Run both reports and save CSVs. Returns the list of paths where files were saved."""
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()
    path1 = download_parts_by_bin_report(
        cookies_path=cookies_path,
        output_path=output_dir / "Parts_By_Bin_Location.csv",
        base_url=base_url,
    )
    path2 = download_parts_price_list_report(
        cookies_path=cookies_path,
        output_path=output_dir / "Parts_Price_List.csv",
        base_url=base_url,
    )
    return [path1, path2]
```

### Example: download both reports in parallel (implement in your project)

Copy this into your project to run both reports concurrently (Promise.all-style):

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from revnext import download_parts_by_bin_report, download_parts_price_list_report


def download_all_reports_parallel(
    cookies_path: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    base_url: Optional[str] = None,
) -> list[Path]:
    """Run both reports in parallel. Returns the list of paths where files were saved."""
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()
    path1 = output_dir / "Parts_By_Bin_Location.csv"
    path2 = output_dir / "Parts_Price_List.csv"
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(
            download_parts_by_bin_report,
            cookies_path=cookies_path,
            output_path=path1,
            base_url=base_url,
        )
        f2 = executor.submit(
            download_parts_price_list_report,
            cookies_path=cookies_path,
            output_path=path2,
            base_url=base_url,
        )
        return [f1.result(), f2.result()]
```

### Using environment variables

Set `REVOLUTIONNEXT_URL` and optionally `REVOLUTIONNEXT_COOKIES_PATH`; then you can omit `base_url` and `cookies_path` in code.

See the [main repo README](https://github.com/Luen/RevNext-TUNE) for full configuration options.
