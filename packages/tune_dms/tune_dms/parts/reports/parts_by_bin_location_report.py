"""Parts by Bin Location report: open and download via TUNE GUI."""

import os
import time

import pyautogui

from tune_dms import screen
from tune_dms.logger import logger_proxy
from tune_dms.parts.reports.params import PartsByBinLocationParams

logger = logger_proxy(__name__)


def open_parts_by_bin_location_report():
    """Navigate to and open the Parts by Bin Location Report in TUNE."""
    try:
        logger.info("Attempting to open Parts by Bin Location Report...")

        for _ in range(2):
            pyautogui.press("down")
        pyautogui.press("enter")

        report_configuration_dialog = screen.waitFor(
            "tune_report_parts_by_bin_location.png"
        )
        if not report_configuration_dialog:
            logger.error("Report configuration dialog not found")
            return False

        logger.info("Parts by Bin Location Report opened successfully")
        return True
    except Exception as e:
        logger.error(f"Error while opening Parts by Bin Location Report: {e}")
        return False


def parts_by_bin_location_report_download(
    params: PartsByBinLocationParams = None, reports_dir: str = None, **kwargs
):
    """
    Download the Parts by Bin Location Report with user-friendly parameter options.

    Args:
        params: A PartsByBinLocationParams object containing all parameters
        reports_dir: Directory where reports will be saved
        **kwargs: Individual parameters that override those in params (if provided)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if reports_dir:
            os.makedirs(reports_dir, exist_ok=True)

        if params is None:
            params = PartsByBinLocationParams(**kwargs)
        elif kwargs:
            for key, value in kwargs.items():
                if hasattr(params, key):
                    setattr(params, key, value)

        if params.output_file_name is None and reports_dir:
            params.output_file_name = "parts_by_bin_location_report.csv"

        params.output_file_path = os.path.join(reports_dir, params.output_file_name)

        if params.to_department is None:
            params.to_department = params.from_department
        if params.to_franchise is None:
            params.to_franchise = params.from_franchise

        logger.info(
            f"Downloading Parts by Bin Location Report with parameters: {params}"
        )

        pyautogui.write(params.from_department)
        pyautogui.press("tab")
        pyautogui.write(params.to_department)
        pyautogui.press("tab")
        pyautogui.write(params.from_franchise)
        pyautogui.press("tab")
        pyautogui.write(params.to_franchise)
        pyautogui.press("tab")
        if params.from_bin:
            pyautogui.write(params.from_bin)
        pyautogui.press("tab")
        if params.to_bin:
            pyautogui.write(params.to_bin)
        pyautogui.press("tab")
        if params.from_movement_code:
            pyautogui.write(params.from_movement_code)
        pyautogui.press("tab")
        if params.to_movement_code:
            pyautogui.write(params.to_movement_code)
        pyautogui.press("tab")
        if params.show_stock_as == "Physical Stock":
            logger.info("Physical Stock selected")
        elif params.show_stock_as == "Available Stock":
            pyautogui.press("down")
        else:
            logger.error(f"Invalid show stock as option: {params.show_stock_as}")

        pyautogui.press("tab")
        if params.print_when_stock_not_zero:
            logger.info("Print when stock not zero checked")
        pyautogui.press("tab")
        if params.print_part_when_stock_is_zero:
            logger.info("Print part when stock is Zero checked")
        pyautogui.press("tab")
        if params.print_part_when_stock_on_order_is_zero:
            logger.info("Print part when stock on order is Zero checked")
        pyautogui.press("tab")
        if params.no_primary_bin_location:
            logger.info("No primary bin location checked")
        pyautogui.press("tab")
        if params.no_alternate_bin_location:
            logger.info("No alternate bin location checked")
        pyautogui.press("tab")
        if params.no_primary_bin_but_has_alternate_bin:
            logger.info("No primary bin, but has an alternate bin checked")
        pyautogui.press("tab")
        if params.has_both_primary_and_alternate_bin_location:
            logger.info("Has both a primary and alternate bin location checked")
        pyautogui.press("tab")
        if params.last_sale_before:
            logger.info("Last sale before checked")
        pyautogui.press("tab")
        if params.last_receipt_before:
            logger.info("Last receipt before checked")
        pyautogui.press("tab")
        if params.print_average_cost:
            pyautogui.press("space")
            logger.info("Print average cost checked")

        pyautogui.press("o")
        time.sleep(0.1)
        if params.output_file_type == "CSV":
            for _ in range(4):
                pyautogui.press("down")
        elif params.output_file_type == "Excel":
            for _ in range(5):
                pyautogui.press("down")
        else:
            logger.error(f"Invalid output file type: {params.output_file_type}")

        pyautogui.press("o")
        save_as_window = screen.waitFor("save_as_window.png", timeout=15)
        if not save_as_window:
            logger.error("Save as window not found")
            return False
        pyautogui.write(params.output_file_path)
        pyautogui.press("enter")

        confirm_save_as_dialog = screen.waitFor("confirm_save_as_dialog.png")
        if confirm_save_as_dialog:
            pyautogui.press("left")
            pyautogui.press("enter")

        start_time = time.time()
        logger.info("Starting report generation...")
        report_success = screen.waitFor("tune_application_screen.png", timeout=60)
        duration = round(time.time() - start_time, 2)
        if not report_success:
            logger.error(
                f"Report generation failed or timed out after {duration} seconds"
            )
            return False
        logger.info(f"Report generation completed in {duration} seconds")

        if not os.path.exists(params.output_file_path):
            logger.error(f"Report file was not created: {params.output_file_path}")
            return False

        time.sleep(1)
        file_size = os.path.getsize(params.output_file_path)
        if file_size == 0:
            logger.error(f"Report file is empty: {params.output_file_path}")
            return False

        logger.info(
            f"Parts by Bin Location Report downloaded successfully (size: {file_size} bytes)"
        )
        return True
    except Exception as e:
        logger.error(
            f"Error while downloading Parts by Bin Location Report: {e}"
        )
        return False
