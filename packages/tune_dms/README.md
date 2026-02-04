# tune-dms

TUNE DMS desktop GUI automation: log in and run reports (e.g. Parts Price List, Parts by Bin Location) via keyboard and screen image matching.

- **Install:** `pip install tune-dms`  
- **Editable (from repo root):** `pip install -e ./packages/tune_dms`

## Configuration

Set credentials (and optional paths) via environment variables or a `.env` file. Optional: use `python-dotenv` so `TuneConfig.from_env()` can load from `.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `TUNE_USER_ID` | Yes | TUNE login user ID |
| `TUNE_USER_PASSWORD` | Yes | TUNE login password |
| `TUNE_SHORTCUT_PATH` | No | Path to TUNE shortcut (default: `C:\Users\Public\Desktop\TUNE.lnk`) |
| `TUNE_REPORTS_DIR` | No | Directory where reports are saved (default: current working directory) |
| `TUNE_IMAGES_DIR` | No | Override path to reference images (default: package `images/`) |

## Usage example

After installing, ensure TUNE is not running and that the desktop/shortcut is as expected. Then load config and run the built-in report workflow:

```python
from tune_dms import TuneConfig, run_tune_reports

# Load from environment (e.g. TUNE_USER_ID, TUNE_USER_PASSWORD in .env or env)
config = TuneConfig.from_env()

# Optional: set reports directory if not using TUNE_REPORTS_DIR
# config = TuneConfig.from_env(reports_dir="C:/path/to/reports")

config.validate()  # raises if user_id/password missing
success = run_tune_reports(config)
```

The runner will:

1. Launch TUNE from the configured shortcut  
2. Log in using the configured credentials  
3. Navigate by department and run **Parts Price List** and **Parts by Bin Location** for each (department/franchise and output filenames are fixed in the built-in workflow)  
4. Close TUNE when done  

For a custom sequence of reports, use `TuneReportGenerator` with the same config and call `run_reports()`; the class uses the same flow internally. Report parameters (department, franchise, output file name, etc.) are set via `PartsPriceListParams` and `PartsByBinLocationParams` when calling the download helpers inside that flow.

## Requirements

- **Windows** (shortcut path and automation are Windows-oriented)
- **pyautogui** (installed with the package)
- TUNE desktop application installed and a desktop shortcut at the configured path
- Reference images are included in the package (`tune_dms/images/`); do not move the package’s `images` folder if using the default `TUNE_IMAGES_DIR`

See the [main repo](https://github.com/Luen/RevNext-TUNE) for more context and the monorepo layout.
