# RevNext and TUNE

Mono repo for **TUNE DMS** (desktop GUI automation) and **REVOLUTIONnext SmartCenter** (`*.revolutionnext.com.au`).

- **tune-dms** – TUNE DMS: log in via the GUI and run reports (Parts Price List, Parts by Bin Location) using keyboard/screen automation. Reference images are in `packages/tune_dms/tune_dms/images/`.
- **revnext** – Revolution Next: download the same reports via HTTP (cookies/session). Use this when you only need RevNext or want to avoid the GUI.

## Two separate libraries

| Install | Use case |
|--------|----------|
| `pip install tune-dms` | TUNE DMS automation only |
| `pip install revnext` | RevNext report downloads only |

Install both if you need both: `pip install tune-dms revnext`

**From this repo (editable install):**

```bash
# One or both (from repo root):
pip install -e ./packages/tune_dms
pip install -e ./packages/revnext
```

TUNE reference images live in **`packages/tune_dms/tune_dms/images/`** and are bundled with the package when you install.

## Configuration

Use environment variables and/or pass config in code.

### TUNE (tune-dms)

| Variable | Description |
|----------|-------------|
| `TUNE_USER_ID` | TUNE DMS login user ID |
| `TUNE_USER_PASSWORD` | TUNE DMS login password |
| `TUNE_SHORTCUT_PATH` | (Optional) Path to TUNE shortcut |
| `TUNE_IMAGES_DIR` | (Optional) Override images directory (default: `tune_dms/images/` inside the package) |
| `TUNE_REPORTS_DIR` | (Optional) Where to save reports |

**In code:**

```python
from tune_dms import TuneConfig, run_tune_reports

config = TuneConfig.from_env()
# or: config = TuneConfig(user_id="...", password="...", reports_dir="/path")
config.validate()
run_tune_reports(config)
```

### RevNext (revnext)

| Variable | Description |
|----------|-------------|
| `REVOLUTIONNEXT_URL` | Base URL, e.g. `https://yoursite.revolutionnext.com.au` |
| `REVOLUTIONNEXT_COOKIES_PATH` | (Optional) Path to cookies JSON (Chrome export) |

**In code:**

```python
from revnext import download_all_reports, RevNextConfig
from pathlib import Path

download_all_reports(
    cookies_path=Path("revnext-cookies.json"),
    output_dir=Path("reports"),
    base_url="https://yoursite.revolutionnext.com.au",
)
```

## Usage overview

**TUNE (tune-dms)**  
- Ensure TUNE is not running (or will be controlled by the script).  
- Images are in `packages/tune_dms/tune_dms/images/` (or set `TUNE_IMAGES_DIR` to override).  
- Call `run_tune_reports(config)` to launch TUNE, log in, and run the built-in report sequence.

**RevNext (revnext)**  
- Export cookies for your RevNext domain (e.g. Chrome → export as JSON).  
- Set `REVOLUTIONNEXT_URL` or pass `base_url` to the download functions.  
- Use `download_parts_price_list_report`, `download_parts_by_bin_report`, or `download_all_reports`.

## Project layout

- **packages/tune_dms/** – TUNE-only package (`pip install tune-dms`). Reference images in `tune_dms/images/`.
- **packages/revnext/** – RevNext-only package (`pip install revnext`).

Copy `.env.template` to `.env` and set the variables you need for TUNE and/or RevNext.

## Publishing to PyPI

CI publishes to PyPI and creates a GitHub Release when you **bump the version** in a package’s `pyproject.toml` and push to `main` (or `master`).

1. Bump the version in the package’s `pyproject.toml` (e.g. `0.1.0` → `0.1.1`).
2. Commit and push to `main`.

The matching workflow runs only when that package’s `pyproject.toml` changes. It reads the new version, creates a tag (e.g. `tune-dms-v0.1.1` or `revnext-v0.1.1`), builds the package, uploads to PyPI, and creates a GitHub Release. If a tag for that version already exists, the workflow skips publishing. Ensure the repo secret **`PYPI_API_TOKEN`** is set (PyPI API token with scope for the project).
