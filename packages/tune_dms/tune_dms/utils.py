"""
Report generation orchestration: run the full TUNE report workflow.
Uses app (launch/login/close/reset) and parts.reports.
"""

import os
import time
import logging
import traceback

import pyautogui

from tune_dms.config import TuneConfig
from tune_dms import app
from tune_dms.parts.reports import (
    PartsPriceListParams,
    PartsByBinLocationParams,
    open_parts_price_list_report,
    parts_price_list_report_download,
    open_parts_by_bin_location_report,
    parts_by_bin_location_report_download,
)

logger = logging.getLogger(__name__)


class TuneReportGenerator:
    """Generates reports from the TUNE system."""

    def __init__(self, config: TuneConfig):
        self.config = config

    def run_reports(self) -> bool:
        """Run the TUNE launcher to download the required reports."""
        logger.info("Starting TUNE report generation...")
        reports_dir = self.config.reports_dir or os.getcwd()
        try:
            reset_ok = app.reset_tune_to_startup(
                department_index=self.config.department_index,
                division_index=self.config.division_index,
                company_index=self.config.company_index,
            )
            if reset_ok:
                time.sleep(1)
            else:
                app.launch_tune_application()
                time.sleep(3)
                login_success = app.login_to_tune()
                if not login_success:
                    logger.error("Failed to login to TUNE. Exiting.")
                    return False
            time.sleep(2)

            # Select 130 Department - MCT Parts and Accessories
            for _ in range(3):
                pyautogui.press("tab")
                time.sleep(0.1)
            for _ in range(6):
                pyautogui.press("up")
                time.sleep(0.1)
            for _ in range(5):
                pyautogui.press("tab")

            # Generate Parts Price List Report
            logger.info("Generating Parts Price List Report...")
            report_success = open_parts_price_list_report()
            if report_success:
                params = PartsPriceListParams(
                    from_department="130",
                    from_franchise="TOY",
                    output_file_name="Parts Price List Report - 130.csv",
                )
                download_success = parts_price_list_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error("Failed to download Parts Price List Report")
                    app.close_tune_application()
                    return False
                logger.info("Parts Price List Report generated successfully")
            else:
                logger.error("Failed to open Parts Price List Report")
                app.close_tune_application()
                return False

            # Generate Parts by Bin Location Report
            logger.info("Generating Parts by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                params = PartsByBinLocationParams(
                    from_department="130",
                    from_franchise="TOY",
                    show_stock_as="Available Stock",
                    print_when_stock_not_zero=True,
                    output_file_name="Parts by Bin Location Report - 130.csv",
                )
                download_success = parts_by_bin_location_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error("Failed to download Parts by Bin Location Report")
                    app.close_tune_application()
                    return False
                logger.info("Parts by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Parts by Bin Location Report")
                app.close_tune_application()
                return False

            # Select 145 Department - MCT Tyres
            for _ in range(5):
                pyautogui.hotkey("shift", "tab")
                time.sleep(0.1)
            for _ in range(3):
                pyautogui.press("down")
                time.sleep(0.1)
            for _ in range(5):
                pyautogui.press("tab")

            logger.info("Generating Tyres Price List Report...")
            report_success = open_parts_price_list_report(
                currently_selected_report="Parts By Bin Location"
            )
            if report_success:
                params = PartsPriceListParams(
                    from_department="145",
                    from_franchise="TOY",
                    output_file_name="Parts Price List Report - 145.csv",
                )
                download_success = parts_price_list_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error("Failed to download Tyres Price List Report")
                    app.close_tune_application()
                    return False
                logger.info("Tyres Price List Report generated successfully")
            else:
                logger.error("Failed to open Tyres Price List Report")
                app.close_tune_application()
                return False

            logger.info("Generating Tyres by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                params = PartsByBinLocationParams(
                    from_department="145",
                    from_franchise="TOY",
                    output_file_name="Parts by Bin Location Report - 145.csv",
                )
                download_success = parts_by_bin_location_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error("Failed to download Tyres by Bin Location Report")
                    app.close_tune_application()
                    return False
                logger.info("Tyres by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Tyres by Bin Location Report")
                app.close_tune_application()
                return False

            # Select 330 Department - Ingham Toyota
            for _ in range(5):
                pyautogui.hotkey("shift", "tab")
                time.sleep(0.1)
            for _ in range(7):
                pyautogui.press("down")
                time.sleep(0.1)
            for _ in range(5):
                pyautogui.press("tab")

            logger.info("Generating Ingham Toyota Parts Price List Report...")
            report_success = open_parts_price_list_report(
                currently_selected_report="Parts By Bin Location"
            )
            if report_success:
                params = PartsPriceListParams(
                    from_department="330",
                    from_franchise="TOY",
                    output_file_name="Parts Price List Report - 330.csv",
                )
                download_success = parts_price_list_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error(
                        "Failed to download Ingham Toyota Parts Price List Report"
                    )
                    app.close_tune_application()
                    return False
                logger.info(
                    "Ingham Toyota Parts Price List Report generated successfully"
                )
            else:
                logger.error("Failed to open Ingham Toyota Parts Price List Report")
                app.close_tune_application()
                return False

            logger.info("Generating Ingham Toyota Parts by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                params = PartsByBinLocationParams(
                    from_department="330",
                    from_franchise="TOY",
                    output_file_name="Parts by Bin Location Report - 330.csv",
                )
                download_success = parts_by_bin_location_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error(
                        "Failed to download Ingham Toyota Parts by Bin Location Report"
                    )
                    app.close_tune_application()
                    return False
                logger.info(
                    "Ingham Toyota Parts by Bin Location Report generated successfully"
                )
            else:
                logger.error(
                    "Failed to open Ingham Toyota Parts by Bin Location Report"
                )
                app.close_tune_application()

            # Select Company 04 - Charters Towers Partnership
            for _ in range(7):
                pyautogui.hotkey("shift", "tab")
            pyautogui.press("down")
            logger.info("Selected Company 04 - Charters Towers Partnership")
            time.sleep(2)
            for _ in range(7):
                pyautogui.press("tab")

            logger.info(
                "Generating Charters Towers Partnership Parts Price List Report..."
            )
            report_success = open_parts_price_list_report()
            if report_success:
                params = PartsPriceListParams(
                    from_department="430",
                    from_franchise="TOY",
                    output_file_name="Parts Price List Report - 430.csv",
                )
                download_success = parts_price_list_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error(
                        "Failed to download Charters Towers Partnership Parts Price List Report"
                    )
                    app.close_tune_application()
                    return False
                logger.info(
                    "Charters Towers Partnership Parts Price List Report generated successfully"
                )
            else:
                logger.error(
                    "Failed to open Charters Towers Partnership Parts Price List Report"
                )
                app.close_tune_application()
                return False

            logger.info(
                "Generating Charters Towers Partnership Parts by Bin Location Report..."
            )
            report_success = open_parts_by_bin_location_report()
            if report_success:
                params = PartsByBinLocationParams(
                    from_department="430",
                    from_franchise="TOY",
                    output_file_name="Parts by Bin Location Report - 430.csv",
                )
                download_success = parts_by_bin_location_report_download(
                    params, reports_dir=reports_dir
                )
                if not download_success:
                    logger.error(
                        "Failed to download Charters Towers Partnership Parts by Bin Location Report"
                    )
                    app.close_tune_application()
                    return False
                logger.info(
                    "Charters Towers Partnership Parts by Bin Location Report generated successfully"
                )
            else:
                logger.error(
                    "Failed to open Charters Towers Partnership Parts by Bin Location Report"
                )
                app.close_tune_application()
                return False

            app.close_tune_application()
            logger.info("TUNE reports generation completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during TUNE report generation: {e}")
            traceback.print_exc()
            try:
                app.close_tune_application()
            except Exception:
                pass
            return False
