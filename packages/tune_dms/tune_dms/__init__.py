"""
TUNE DMS: desktop GUI automation for login and report generation.
"""

from tune_dms.config import TuneConfig
from tune_dms.launcher import main as run_tune_reports
from tune_dms.logger import get_logger, set_logger
from tune_dms.utils import (
    TuneReportGenerator,
    PartsPriceListParams,
    PartsByBinLocationParams,
    parts_price_list_report_download,
    parts_by_bin_location_report_download,
)

__all__ = [
    "TuneConfig",
    "run_tune_reports",
    "TuneReportGenerator",
    "PartsPriceListParams",
    "PartsByBinLocationParams",
    "parts_price_list_report_download",
    "parts_by_bin_location_report_download",
    "get_logger",
    "set_logger",
]

__version__ = "0.1.0"
