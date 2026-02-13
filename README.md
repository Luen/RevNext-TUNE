# RevNext and TUNE

Mono repo for **TUNE DMS** (desktop GUI automation) and **REVOLUTIONnext SmartCenter** (`*.revolutionnext.com.au`).

- **[tune-dms](https://pypi.org/project/tune-dms)** – TUNE DMS: log in via the GUI and run reports (Parts Price List, Parts by Bin Location) using keyboard/screen automation. Reference images are in `packages/tune_dms/tune_dms/images/`.
- **[revnext](https://pypi.org/project/revnext)** – Revolution Next: download the same reports via HTTP (cookies/session). Use this when you only need RevNext or want to avoid the GUI.

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
| `REVNEXT_URL` | Base URL, e.g. `https://yourtenant.revolutionnext.com.au` |
| `REVNEXT_USERNAME` | RevNext login User ID |
| `REVNEXT_PASSWORD` | RevNext login Password |
| `REVNEXT_SESSION_PATH` | (Optional) Session cookie file (default: `.revnext-session.json` in cwd) |

**In code:**

```python
from revnext import download_parts_by_bin_report, download_parts_price_list_report
from pathlib import Path

# Uses REVNEXT_URL, REVNEXT_USERNAME, REVNEXT_PASSWORD from env
out = Path("reports")
download_parts_by_bin_report(output_path=out / "Parts_By_Bin_Location.csv")
download_parts_price_list_report(output_path=out / "Parts_Price_List.csv")
```

To run both in one go (or in parallel), see the examples in [packages/revnext/README.md](packages/revnext/README.md).

**Custom logger:** Both **tune_dms** and **revnext** support a custom logger. Call `set_logger(my_logger)` before using the library so all log output uses your handler and format. See each package’s README for a short example.

## Usage overview

**TUNE (tune-dms)**  
- Ensure TUNE is not running (or will be controlled by the script).  
- Images are in `packages/tune_dms/tune_dms/images/` (or set `TUNE_IMAGES_DIR` to override).  
- Call `run_tune_reports(config)` to launch TUNE, log in, and run the built-in report sequence.

**RevNext (revnext)**  
- Set `REVNEXT_URL`, `REVNEXT_USERNAME`, and `REVNEXT_PASSWORD` in `.env` (or environment). Auto-login saves the session to disk; later runs reuse it until invalid.  
- Use `download_parts_price_list_report` and `download_parts_by_bin_report`; see the package README for examples that download both (sequential or parallel).

## Project layout

- **packages/tune_dms/** – TUNE-only package (`pip install tune-dms`). Reference images in `tune_dms/images/`.
- **packages/revnext/** – RevNext-only package (`pip install revnext`).

Copy `.env.template` to `.env` and set the variables you need for TUNE and/or RevNext.

## Publishing to PyPI

CI publishes to PyPI and creates a GitHub Release when you **bump the version** in a package’s `pyproject.toml` and push to `main` (or `master`).

1. Bump the version in the package’s `pyproject.toml` (e.g. `0.1.0` → `0.1.1`).
2. Commit and push to `main`.

The matching workflow runs only when that package’s `pyproject.toml` changes. It reads the new version, creates a tag (e.g. `tune-dms-v0.1.1` or `revnext-v0.1.1`), builds the package, uploads to PyPI, and creates a GitHub Release. If a tag for that version already exists, the workflow skips publishing.

**Required repository secrets:**
- **`PYPI_API_TOKEN`** – PyPI API token for uploading.
- **`REPO_ACCESS_TOKEN`** – A GitHub Personal Access Token (classic) with `repo` scope. The default `GITHUB_TOKEN` cannot push tags when the tagged commit modifies `.github/workflows/`; a PAT avoids that restriction. Create one under [GitHub → Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens), then add it under **Settings → Secrets and variables → Actions**.
