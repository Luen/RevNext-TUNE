# tune-dms

TUNE DMS desktop GUI automation: log in and run **parts reports** (Parts Price List, Parts by Bin Location) via keyboard and screen image matching and also supports **Parts → Sales → Work With Orders**: fill the Add Order form programmatically.

- **Install:** `pip install tune-dms`  
- **Editable (from repo root):** `pip install -e ./packages/tune_dms`

## Contents

- [Configuration](#configuration)
- [Custom logger](#custom-logger)
- [Usage example](#usage-example)
- [Parts Reports](#parts-reports)
  - [Parts Price List](#parts-reports)
  - [Parts by Bin Location](#parts-reports)
- [Parts Sales](#parts-sales)
  - [Work With Orders](#work-with-orders)
- [Requirements](#requirements)
- [Developer reference](#developer-reference)
  - [Package layout](#package-layout)
  - [Public API](#public-api)
  - [Report parameters](#report-parameters)
  - [Work With Orders parameters](#work-with-orders-parameters)

## Configuration

Set credentials (and optional paths) via environment variables or a `.env` file. Optional: use `python-dotenv` so `TuneConfig.from_env()` can load from `.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `TUNE_USER_ID` | Yes | TUNE login user ID |
| `TUNE_USER_PASSWORD` | Yes | TUNE login password |
| `TUNE_SHORTCUT_PATH` | No | Path to TUNE shortcut (default: `C:\Users\Public\Desktop\TUNE.lnk`) |
| `TUNE_REPORTS_DIR` | No | Directory where reports are saved (default: current working directory) |
| `TUNE_IMAGES_DIR` | No | Override path to reference images (default: package `images/`) |

## Custom logger

You can inject your own logger so all library log output uses your handler, level, and format. Call `set_logger(my_logger)` **before** using other tune_dms APIs. Pass `None` to revert to the default.

```python
import logging
from tune_dms import set_logger, TuneConfig, run_tune_reports

logger = logging.getLogger("my_app.tune_dms")
logger.setLevel(logging.INFO)
# add handlers, formatters, etc.
set_logger(logger)

config = TuneConfig.from_env()
run_tune_reports(config)  # all tune_dms logs go to your logger
```

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

## Parts Reports

Two report types are supported; both use GUI automation (keyboard + screen image matching).

| Report | Open function | Download function | Params class |
|--------|----------------|-------------------|--------------|
| **Parts Price List** | `open_parts_price_list_report()` | `parts_price_list_report_download()` | `PartsPriceListParams` |
| **Parts by Bin Location** | `open_parts_by_bin_location_report()` | `parts_by_bin_location_report_download()` | `PartsByBinLocationParams` |

- **Open functions:** Navigate to and open the report configuration dialog in TUNE. The app must be logged in and at the correct menu. `open_parts_price_list_report(currently_selected_report="Parts By Bin Location")` uses shorter navigation when the list is already on Parts By Bin Location.
- **Download functions:** Fill the dialog from a params instance (or `**kwargs`), trigger Save, and wait for the file. Pass `params=...` and `reports_dir=...`; if `output_file_name` is `None` and `reports_dir` is set, defaults are `parts_price_list_report.csv` and `parts_by_bin_location_report.csv`.

Import from `tune_dms` (params and download functions) or `tune_dms.parts.reports` (open functions too):

```python
from tune_dms import (
    PartsPriceListParams,
    PartsByBinLocationParams,
    parts_price_list_report_download,
    parts_by_bin_location_report_download,
)
from tune_dms.parts.reports import open_parts_price_list_report, open_parts_by_bin_location_report

reports_dir = "C:/Reports"
params_pl = PartsPriceListParams(
    from_department="130",
    from_franchise="TOY",
    output_file_name="Parts Price List - 130.csv",
)
ok = parts_price_list_report_download(params_pl, reports_dir=reports_dir)

params_bin = PartsByBinLocationParams(
    from_department="130",
    from_franchise="TOY",
    show_stock_as="Available Stock",
    output_file_type="CSV",
    output_file_name="Parts by Bin Location - 130.csv",
)
ok = parts_by_bin_location_report_download(params_bin, reports_dir=reports_dir)
```

## Parts sales

Parts → Sales menu automation (e.g. Work With Orders).

### Work With Orders

Fill the **Add Order** form in **Parts → Sales → Work With Orders** via GUI automation. Assumes TUNE is open and **Work With Orders** is already on screen.

Import from `tune_dms.parts.sales`:

```python
from tune_dms.parts.sales import WorkWithOrderParams, fill_add_order_form

params = WorkWithOrderParams(
    customer_id="12345",
    phone="0412345678",
    contact="John Smith",
    email="john@example.com",
    date_reqd="01/12/25",
    address_line_1="123 Main St",
    state="QLD",
    postal_code="4000",
    customer_po="SHOP-ORDER-001",
)
success = fill_add_order_form(params)
```

- **Prerequisites:** Parts → Sales → Work With Orders must be open and focused. The function presses Add, then fills the form. Phone and email are normalized (e.g. `+61` → `0`).
- **Validation:** If a validation error dialog is detected, the script prompts in the terminal to fix it in TUNE and press Enter to continue. You may also be prompted to confirm and enter parts before submit.
- **Optional fields:** `sales_rep`, `order_type`, `order_note`, `ship_to`, `address_unknown`, `freight_terms`, `backorder_action`, `ship_via_index`, `tax_type_index`, `prefilled_data`, `skip_address_validation`. See `WorkWithOrderParams` in `tune_dms.parts.sales.work_with_orders`.

## Requirements

- **Windows** (shortcut path and automation are Windows-oriented)
- **pyautogui** (installed with the package)
- TUNE desktop application installed and a desktop shortcut at the configured path
- Reference images are included in the package (`tune_dms/images/`); do not move the package’s `images` folder if using the default `TUNE_IMAGES_DIR`

## Developer reference

### Package layout

| Path | Purpose |
|------|--------|
| `tune_dms` | Top-level: config, logger, run_tune_reports, TuneReportGenerator, report params and download functions |
| `tune_dms.config` | `TuneConfig`, `TuneConfig.from_env()`, `validate()` |
| `tune_dms.logger` | `get_logger`, `set_logger` |
| `tune_dms.launcher` | `main` (as `run_tune_reports`) – launch, login, built-in report workflow, close |
| `tune_dms.utils` | `TuneReportGenerator`, re-exports report params and download functions |
| `tune_dms.app` | Launch, login, close, reset TUNE |
| `tune_dms.screen` | Screen image matching / wait for images |
| `tune_dms.parts.reports` | Params, open_* and *_download functions for Parts Price List and Parts by Bin Location |
| `tune_dms.parts.reports.params` | `PartsPriceListParams`, `PartsByBinLocationParams` |
| `tune_dms.parts.reports.parts_price_list_report` | Parts Price List implementation |
| `tune_dms.parts.reports.parts_by_bin_location_report` | Parts by Bin Location implementation |
| `tune_dms.parts.sales` | `WorkWithOrderParams`, `fill_add_order_form` |
| `tune_dms.parts.sales.work_with_orders` | Work With Orders form-fill implementation |

### Public API

- **Config:** `TuneConfig`, `TuneConfig.from_env()`, `config.validate()`
- **Logging:** `set_logger(logger)`, `get_logger(name)`
- **Runner:** `run_tune_reports(config)` – built-in workflow
- **Custom reports:** `TuneReportGenerator(config).run_reports()`
- **Reports:** `parts_price_list_report_download()`, `parts_by_bin_location_report_download()`; params: `PartsPriceListParams`, `PartsByBinLocationParams` (from `tune_dms` or `tune_dms.parts.reports`)
- **Reports (open):** `open_parts_price_list_report()`, `open_parts_by_bin_location_report()` (from `tune_dms.parts.reports`)
- **Work With Orders:** `fill_add_order_form(params)`, `WorkWithOrderParams` (from `tune_dms.parts.sales`)

### Report parameters

**PartsPriceListParams** – Required: `from_department`, `from_franchise`. `to_franchise` defaults to `from_franchise` if `None`. Optional: `from_bin`, `to_bin`; `price_1` (e.g. `"List"`), `price_2` (e.g. `"Stock"`); `include_gst`; `output_file_type` (`"CSV"` or `"Excel"`); `output_file_name`.

**PartsByBinLocationParams** – Required: `from_department`; default `from_franchise="TOY"`. `to_department`/`to_franchise` default to from_* if `None`. Optional: `from_bin`, `to_bin`, movement codes; `show_stock_as` (`"Physical Stock"` or `"Available Stock"`); print and bin filters; `last_sale_before`, `last_receipt_before`; `print_average_cost`; `report_format`; `output_file_type`; `output_file_name`.

Both download functions accept `params=...`, `reports_dir=...`, and `**kwargs` to override params.

### Work With Orders parameters

**WorkWithOrderParams** – Required: `customer_id`. Optional: `sales_rep`, `order_type`, `phone`, `contact`, `email`, `date_reqd` (normalized to DDMMYY), `order_note`, address fields, `ship_to`, `customer_po`; `freight_terms`, `backorder_action`; `ship_via_index`, `tax_type_index`; `prefilled_data`, `skip_address_validation`. Phone/email normalized (e.g. `+61` → `0`). Form flow may pause for validation or for you to confirm and enter parts.

See the [main repo](https://github.com/Luen/RevNext-TUNE) for more context and the monorepo layout.
