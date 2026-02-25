"""Parts Price List report: open and download via TUNE GUI."""

import os
import time
import pyautogui

from tune_dms import screen
from tune_dms.logger import logger_proxy
from tune_dms.parts.reports.params import PartsPriceListParams

logger = logger_proxy(__name__)


def open_parts_price_list_report(currently_selected_report: str = None):
    """
    Navigate to and open the Parts Price List Report in TUNE by using keyboard navigation.

    Returns:
        bool: True if the operation was attempted, False otherwise
    """
    try:
        logger.info("Attempting to open Parts Price List Report...")

        if currently_selected_report == "Parts By Bin Location":
            for _ in range(2):
                pyautogui.press("up")
            pyautogui.press("enter")
            logger.info("Opening the report configuration dialog")
            return True

        for _ in range(6):
            pyautogui.press("down")
        pyautogui.press("right")
        for _ in range(5):
            pyautogui.press("down")
        pyautogui.press("right")
        for _ in range(16):
            pyautogui.press("down")
        pyautogui.press("enter")
        logger.info("Opening the report configuration dialog")

        report_configuration_dialog = screen.waitFor("tune_report_parts_price_list.png")
        if not report_configuration_dialog:
            logger.error("Report configuration dialog not found")
            return False

        logger.info("Parts Price List Report navigation sequence executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error while opening Parts Price List Report: {e}")
        return False


def parts_price_list_report_download(
    params: PartsPriceListParams = None, reports_dir: str = None, **kwargs
):
    """
    Download the Parts Price List Report with user-friendly parameter options.

    Args:
        params: A PartsPriceListParams object containing all parameters
        reports_dir: Directory where reports will be saved
        **kwargs: Individual parameters that override those in params (if provided)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if reports_dir:
            os.makedirs(reports_dir, exist_ok=True)

        if params is None:
            params = PartsPriceListParams(**kwargs)
        elif kwargs:
            for key, value in kwargs.items():
                if hasattr(params, key):
                    setattr(params, key, value)

        if params.output_file_name is None and reports_dir:
            params.output_file_name = "parts_price_list_report.csv"

        params.output_file_path = os.path.join(reports_dir, params.output_file_name)

        if params.to_franchise is None:
            params.to_franchise = params.from_franchise

        logger.info(f"Downloading Parts Price List Report with parameters: {params}")

        pyautogui.press("tab")
        pyautogui.write(params.from_department)
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
        if params.price_1 == "List":
            for _ in range(2):
                pyautogui.press("down")
        else:
            logger.error(f"Invalid price type: {params.price_1}")

        pyautogui.press("tab")
        if params.price_2 == "Stock":
            for _ in range(25):
                pyautogui.press("down")
            pyautogui.press("enter")
        else:
            logger.error(f"Invalid price type: {params.price_2}")

        pyautogui.press("tab")
        if params.include_gst:
            pyautogui.press("space")
        pyautogui.press("tab")
        if params.include_gst:
            pyautogui.press("space")

        pyautogui.press("o")
        if params.output_file_type == "CSV":
            for _ in range(4):
                pyautogui.press("down")
        elif params.output_file_type == "Excel":
            for _ in range(5):
                pyautogui.press("down")
        else:
            logger.error(f"Invalid output file type: {params.output_file_type}")

        time.sleep(0.1)
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
        report_success = screen.waitFor("tune_application_screen.png", timeout=80)
        duration = round(time.time() - start_time, 2)
        if not report_success:
            logger.error(f"Report FAILED after {duration} seconds")
        else:
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
            f"Parts Price List Report downloaded successfully (size: {file_size} bytes)"
        )
        return True
    except Exception as e:
        logger.error(f"Error while downloading Parts Price List Report: {e}")
        return False
