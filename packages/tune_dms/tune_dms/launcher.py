import subprocess
import os
import time
import pyautogui
import logging
from dataclasses import dataclass
from typing import Optional, Literal
import traceback
import sys

from tune_dms.config import TuneConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set by main() so that login_to_tune, launch_tune_application, and waitFor use it
_config: Optional[TuneConfig] = None


def _get_images_dir() -> str:
    """Return the images directory from config or package default (tune_dms/images/)."""
    if _config and _config.images_dir:
        return _config.images_dir
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pkg_dir, "images")

# Define dataclasses for report parameters
@dataclass
class PartsPriceListParams:
    from_department: str
    from_franchise: str
    to_franchise: str = None  # Default to same as from_franchise if None
    from_bin: Optional[str] = None
    to_bin: Optional[str] = None
    price_1: Literal["List"] = "List"
    price_2: Literal["Stock"] = "Stock"
    include_gst: bool = True
    output_file_type: Literal["CSV", "Excel"] = "CSV"
    output_file_name: str = None  # Will be set in the function

@dataclass
class PartsByBinLocationParams:
    from_department: str
    to_department: Optional[str] = None  # Default to same as from_department if None
    from_franchise: str = "TOY"
    to_franchise: Optional[str] = None  # Default to same as from_franchise if None
    from_bin: Optional[str] = None
    to_bin: Optional[str] = None
    from_movement_code: Optional[str] = None
    to_movement_code: Optional[str] = None
    show_stock_as: Literal["Physical Stock", "Available Stock"] = "Physical Stock"
    print_when_stock_not_zero: bool = True
    print_part_when_stock_is_zero: bool = False
    print_part_when_stock_on_order_is_zero: bool = False
    no_primary_bin_location: bool = False
    no_alternate_bin_location: bool = False
    no_primary_bin_but_has_alternate_bin: bool = False
    has_both_primary_and_alternate_bin_location: bool = False
    last_sale_before: Optional[str] = None
    last_receipt_before: Optional[str] = None
    print_average_cost: bool = False
    report_format: Literal["Split departments onto new page", "Print all departments on one page"] = "Split departments onto new page"
    output_file_type: Literal["CSV", "Excel"] = "CSV"
    output_file_name: str = None  # Will be set in the function

def waitFor(image_name, timeout=10, confidence=0.9):
    """
    Wait for an image to appear on screen.
    
    Args:
        image_name (str): Name of the image file in the images directory
        timeout (int): Maximum time to wait in seconds
        confidence (float): Confidence level for image matching (0-1)
        
    Returns:
        tuple or None: Position of the image if found, None otherwise
    """
    image_path = os.path.join(_get_images_dir(), image_name)
    logger.info(f"Waiting for image: {image_path}")
    
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            position = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if position:
                logger.info(f"Found image at position: {position}")
                return position
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            logger.error(f"Error finding image: {e}")
            return None
        
        time.sleep(0.5)
    
    logger.warning(f"Image not found after {timeout} seconds: {image_path}")
    return None

def open_parts_price_list_report(currently_selected_report: str = None):
    """
    Navigate to and open the Parts Price List Report in TUNE
    by using keyboard navigation
    
    Returns:
        bool: True if the operation was attempted, False otherwise
    """
    try:
        logger.info("Attempting to open Parts Price List Report...")

        if currently_selected_report == 'Parts By Bin Location':
            for i in range(2):
                pyautogui.press('up')
            # Press Enter to select the menu item
            pyautogui.press('enter')
            logger.info("Opening the report configuration dialog")
            return True

        
        # Press Down arrow key 6 times to Parts
        for i in range(6):
            pyautogui.press('down')
        
        # Open Parts folder
        pyautogui.press('right')

        # Press Down arrow key 1 time to Parts
        for i in range(5):
            pyautogui.press('down')

        # Open reports folder
        pyautogui.press('right')
        
        # Open Parts Price List Report
        for i in range(16):
            pyautogui.press('down')
        
        # Press Enter to select the menu item
        pyautogui.press('enter')
        logger.info("Opening the report configuration dialog")

        # Wait for the report configuration dialog to open
        report_configuration_dialog = waitFor('tune_report_parts_price_list.png')
        if not report_configuration_dialog:
            logger.error("Report configuration dialog not found")
            return False
        
        logger.info("Parts Price Pist Peport navigation sequence executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error while opening Parts Price List Report: {e}")
        return False

def parts_price_list_report_download(params: PartsPriceListParams = None, reports_dir: str = None, **kwargs):
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
        # Create reports directory if it doesn't exist
        if reports_dir:
            os.makedirs(reports_dir, exist_ok=True)
        
        # Allow creating params from kwargs or updating the provided params
        if params is None:
            params = PartsPriceListParams(**kwargs)
        elif kwargs:
            # Update params with any provided kwargs
            for key, value in kwargs.items():
                if hasattr(params, key):
                    setattr(params, key, value)
        
        # Set output file name if not provided
        if params.output_file_name is None and reports_dir:
            params.output_file_name = "parts_price_list_report.csv"

        # Set output file path
        params.output_file_path = os.path.join(reports_dir, params.output_file_name)
        
        # Auto-populate to_franchise if not provided
        if params.to_franchise is None:
            params.to_franchise = params.from_franchise
            
        logger.info(f"Downloading Parts Price List Report with parameters: {params}")

        # Start navigating the form
        pyautogui.press('tab')
        pyautogui.write(params.from_department)

        pyautogui.press('tab')
        pyautogui.write(params.from_franchise)

        pyautogui.press('tab')
        pyautogui.write(params.to_franchise)

        pyautogui.press('tab')
        if params.from_bin:
            pyautogui.write(params.from_bin)

        pyautogui.press('tab')
        if params.to_bin:
            pyautogui.write(params.to_bin)

        pyautogui.press('tab')
        if params.price_1 == 'List':
            for i in range(2):
                pyautogui.press('down')
        else:
            logger.error(f"Invalid price type: {params.price_1}")

        pyautogui.press('tab')
        if params.price_2 == 'Stock':
            for i in range(25):
                pyautogui.press('down')
            pyautogui.press('enter')
        else:
            logger.error(f"Invalid price type: {params.price_2}")

        pyautogui.press('tab')
        if params.include_gst:
            pyautogui.press('space')
        pyautogui.press('tab')
        if params.include_gst:
            pyautogui.press('space')

        pyautogui.press('o')

        if params.output_file_type == 'CSV':
            for i in range(4):
                pyautogui.press('down')
        elif params.output_file_type == 'Excel':
            for i in range(5):
                pyautogui.press('down')
        else:
            logger.error(f"Invalid output file type: {params.output_file_type}")

        time.sleep(0.1)

        pyautogui.press('o')
        save_as_window = waitFor('save_as_window.png', timeout=15)
        if not save_as_window:
            logger.error("Save as window not found")
            return False
        pyautogui.write(params.output_file_path)
        pyautogui.press('enter')

        # Overwrite the file if it already exists
        confirm_save_as_dialog = waitFor('confirm_save_as_dialog.png')
        if confirm_save_as_dialog:
            pyautogui.press('left')
            pyautogui.press('enter')

        # Start timing the report generation
        start_time = time.time()
        logger.info("Starting report generation...")
        # Wait for report to finish
        report_success = waitFor('tune_application_screen.png', timeout=80)
        # Calculate and log the duration
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        if not report_success:
            logger.error(f"Report FAILED after {duration} seconds")
        else:
            logger.info(f"Report generation completed in {duration} seconds")
        
        # Verify the file exists and has content
        if not os.path.exists(params.output_file_path):
            logger.error(f"Report file was not created: {params.output_file_path}")
            return False
            
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        # Check file size
        file_size = os.path.getsize(params.output_file_path)
        if file_size == 0:
            logger.error(f"Report file is empty: {params.output_file_path}")
            return False
            
        logger.info(f"Parts Price List Report downloaded successfully (size: {file_size} bytes)")

        '''
        # Check if user clicked and report opened
        report_open = waitFor('tune_admin_purchase_orders_icon_selected.png', timeout=15)
        if report_open:
            logger.info("Report is open, closing it now")
            # Find and click on the "Previous" button to close the report
            previous_button = waitFor('tune_work_with_purchase_orders.png')
            if previous_button:
                pyautogui.click(pyautogui.center(previous_button))
                logger.info("Clicked on Previous button")
                time.sleep(0.5)
                logger.info("Report closed")
        '''

        return True
    except Exception as e:
        logger.error(f"Error while downloading Parts Price List Report: {e}")
        return False

def open_parts_by_bin_location_report():
    """
    Navigate to and open the Parts by Bin Location Report in TUNE
    """
    try:
        logger.info("Attempting to open Parts by Bin Location Report...")

        # Press Down arrow key 2 times to Parts
        for i in range(2):
            pyautogui.press('down')

        # Press Enter to select the menu item
        pyautogui.press('enter')

        # Wait for the report configuration dialog to open
        report_configuration_dialog = waitFor('tune_report_parts_by_bin_location.png')
        if not report_configuration_dialog:
            logger.error("Report configuration dialog not found")
            return False

        logger.info("Parts by Bin Location Report opened successfully")
        return True
    except Exception as e:
        logger.error(f"Error while opening Parts by Bin Location Report: {e}")
        return False

def parts_by_bin_location_report_download(params: PartsByBinLocationParams = None, reports_dir: str = None, **kwargs):
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
        # Create reports directory if it doesn't exist
        if reports_dir:
            os.makedirs(reports_dir, exist_ok=True)
        
        # Allow creating params from kwargs or updating the provided params
        if params is None:
            params = PartsByBinLocationParams(**kwargs)
        elif kwargs:
            # Update params with any provided kwargs
            for key, value in kwargs.items():
                if hasattr(params, key):
                    setattr(params, key, value)
        
        # Set output file name if not provided
        if params.output_file_name is None and reports_dir:
            params.output_file_name = "parts_by_bin_location_report.csv"
        
        # Set output file path
        params.output_file_path = os.path.join(reports_dir, params.output_file_name)
        
        # Auto-populate defaults if not provided
        if params.to_department is None:
            params.to_department = params.from_department
            
        if params.to_franchise is None:
            params.to_franchise = params.from_franchise
            
        logger.info(f"Downloading Parts by Bin Location Report with parameters: {params}")

        # Tab to Department
        pyautogui.write(params.from_department)
        
        # Tab to To Department
        pyautogui.press('tab')
        pyautogui.write(params.to_department)
        
        # Tab to Franchise
        pyautogui.press('tab')
        pyautogui.write(params.from_franchise)
        
        # Tab to To Franchise
        pyautogui.press('tab')
        pyautogui.write(params.to_franchise)
        
        # Tab to From Bin
        pyautogui.press('tab')
        if params.from_bin:
            pyautogui.write(params.from_bin)
        
        # Tab to To Bin
        pyautogui.press('tab')
        if params.to_bin:
            pyautogui.write(params.to_bin)
        
        # Tab to From Movement Code
        pyautogui.press('tab')
        if params.from_movement_code:
            pyautogui.write(params.from_movement_code)
        
        # Tab to To Movement Code
        pyautogui.press('tab')
        if params.to_movement_code:
            pyautogui.write(params.to_movement_code)
        
        # Tab to Show Stock As
        pyautogui.press('tab')
        if params.show_stock_as == "Physical Stock":
            logger.info("Physical Stock selected")            
        elif params.show_stock_as == "Available Stock":
            pyautogui.press('down')
        else:
            logger.error(f"Invalid show stock as option: {params.show_stock_as}")
        
        # Tab to Print When Stock Not Zero
        pyautogui.press('tab')
        if params.print_when_stock_not_zero:
            logger.info("Print when stock not zero checked")
        
        # Tab to Print part when stock is Zero
        pyautogui.press('tab')
        if params.print_part_when_stock_is_zero:
            logger.info("Print part when stock is Zero checked")
        
        # Tab to Print part when STOCK ON ORDER is ZERO
        pyautogui.press('tab')
        if params.print_part_when_stock_on_order_is_zero:
            logger.info("Print part when stock on order is Zero checked")

        # Tab to NO PRIMARY bin location
        pyautogui.press('tab')
        if params.no_primary_bin_location:
            logger.info("No primary bin location checked")

        # Tab to NO ALTERNATE bin location
        pyautogui.press('tab')
        if params.no_alternate_bin_location:
            logger.info("No alternate bin location checked")

        # Tab to NO PRIMARY bin, but has an ALTERNATE bin location
        pyautogui.press('tab')
        if params.no_primary_bin_but_has_alternate_bin:
            logger.info("No primary bin, but has an alternate bin checked")

        # Tab to has BOTH a PRIMARY and ALTERNATE bin location
        pyautogui.press('tab')
        if params.has_both_primary_and_alternate_bin_location:
            logger.info("Has both a primary and alternate bin location checked")

        # Tab to Last Sale Before (Date)
        pyautogui.press('tab')
        if params.last_sale_before:
            logger.info("Last sale before checked")

        # Tab to Last Receipt Before Date
        pyautogui.press('tab')
        if params.last_receipt_before:
            logger.info("Last receipt before checked")

        # Tab to Print Average Cost
        pyautogui.press('tab')
        if params.print_average_cost:
            pyautogui.press('space')
            logger.info("Print average cost checked")
        
        # Tab to Report format
        #pyautogui.press('tab')
        #if params.report_format == 'Split departments onto new page':
        #    logger.info("Split departments onto new page")
        #elif params.report_format == 'Print all departments on one page':
        #    logger.info("Print all departments on one page")
        #else:
        #    logger.error(f"Invalid report format: {params.report_format}")

        # Tab to OK
        #pyautogui.press('tab')
        #pyautogui.press('enter')
        pyautogui.press('o')
        time.sleep(0.1)
        # Select output type
        if params.output_file_type == 'CSV':
            for i in range(4):
                pyautogui.press('down')
        elif params.output_file_type == 'Excel':
            for i in range(5):
                pyautogui.press('down')
        else:
            logger.error(f"Invalid output file type: {params.output_file_type}")
        
        # Select Output
        pyautogui.press('o')
        save_as_window = waitFor('save_as_window.png', timeout=15)
        if not save_as_window:
            logger.error("Save as window not found")
            return False
        pyautogui.write(params.output_file_path)
        pyautogui.press('enter')

        # Overwrite the file if it already exists
        confirm_save_as_dialog = waitFor('confirm_save_as_dialog.png')
        if confirm_save_as_dialog:
            pyautogui.press('left')
            pyautogui.press('enter')
        
        # Start timing the report generation
        start_time = time.time()
        logger.info("Starting report generation...")
        # Wait for report to finish
        report_success = waitFor('tune_application_screen.png', timeout=60)
        # Calculate and log the duration
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        if not report_success:
            logger.error(f"Report generation failed or timed out after {duration} seconds")
            return False
        else:
            logger.info(f"Report generation completed in {duration} seconds")
            
        # Verify the file exists and has content
        if not os.path.exists(params.output_file_path):
            logger.error(f"Report file was not created: {params.output_file_path}")
            return False
            
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        # Check file size
        file_size = os.path.getsize(params.output_file_path)
        if file_size == 0:
            logger.error(f"Report file is empty: {params.output_file_path}")
            return False
            
        logger.info(f"Parts by Bin Location Report downloaded successfully (size: {file_size} bytes)")
        return True
    except Exception as e:
        logger.error(f"Error while downloading Parts by Bin Location Report: {e}")
        return False

def close_tune_application():
    """
    Close TUNE application using Alt, Down, E keyboard shortcut
    
    Returns:
        bool: True if the operation was attempted, False otherwise
    """
    try:
        logger.info("Attempting to close TUNE application...")
        
        # Press Alt key
        pyautogui.press('alt')
        time.sleep(0.3)
        
        # Press Down arrow key
        pyautogui.press('down')
        time.sleep(0.3)
        
        # Press E key
        pyautogui.press('e')
        
        logger.info("TUNE close sequence executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error while closing TUNE: {e}")
        return False

def launch_tune_application():
    """Launch the TUNE software application using the shortcut (path from config)."""
    global _config
    if not _config:
        raise RuntimeError("TUNE config not set. Call run_tune_reports(config) first.")
    logger.info("Launching TUNE software using shortcut...")
    shortcut_path = _config.shortcut_path
    try:
        if not os.path.exists(shortcut_path):
            logger.error(f"TUNE shortcut not found at {shortcut_path}")
            raise FileNotFoundError(f"TUNE shortcut not found at {shortcut_path}")
        
        # Start the TUNE process using the shortcut
        process = subprocess.Popen(f'start "" "{shortcut_path}"', shell=True)
        logger.info("TUNE process started using shortcut")
        return process
    except Exception as e:
        logger.error(f"Failed to launch TUNE: {e}")
        raise

def login_to_tune():
    """Login to TUNE using credentials from config (set by run_tune_reports)."""
    global _config
    if not _config:
        raise RuntimeError("TUNE config not set. Call run_tune_reports(config) first.")
    logger.info("Attempting to login to TUNE...")
    login_screen = waitFor('tune_login_screen.png')
    if not login_screen:
        logger.error("Login screen not found")
        return False
    pyautogui.click(pyautogui.center(login_screen))
    time.sleep(0.5)
    if waitFor('tune_login_screen_environment.png', timeout=1):
        logger.info("TUNE Environment not selected, selecting")
        time.sleep(0.2)
        pyautogui.press('e')
        time.sleep(0.2)
        pyautogui.press('down')
        time.sleep(0.2)
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.write(_config.user_id)
    logger.info("Entered User ID")
    time.sleep(0.5)
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.write(_config.password)
    logger.info("Entered Password")
    time.sleep(0.5)
    
    # Press Enter to submit login
    pyautogui.press('enter')
    logger.info("Submitted login form")

    # Check if login failed
    login_error = waitFor('tune_login_error.png', timeout=3)
    if login_error:
        logger.error("Login failed")
        time.sleep(2)
        pyautogui.press('space')
        return False
    
    # Wait for the application screen to appear
    app_screen = waitFor('tune_application_screen.png', timeout=30)  # Longer timeout for application loading
    if not app_screen:
        logger.error("Application screen not found after login")
        return False
    
    logger.info("Successfully logged into TUNE")
    return True

class TuneReportGenerator:
    """Generates reports from the TUNE system."""

    def __init__(self, config: TuneConfig):
        self.config = config

    def run_reports(self) -> bool:
        """Run the TUNE launcher to download the required reports."""
        logger.info("Starting TUNE report generation...")
        reports_dir = self.config.reports_dir or os.getcwd()
        try:
            # Launch TUNE
            launch_tune_application()
            time.sleep(3)
            # Login to TUNE
            login_success = login_to_tune()
            if not login_success:
                logger.error("Failed to login to TUNE. Exiting.")
                return False
            time.sleep(2)
            # Select 130 Department - MCT Parts and Accessories
            for i in range(3):
                pyautogui.press('tab')
                time.sleep(0.1)
            for i in range(6):
                pyautogui.press('up')
                time.sleep(0.1)

            # Move to menu
            for i in range(5):
                pyautogui.press('tab')

            # Generate Parts Price List Report
            logger.info("Generating Parts Price List Report...")
            report_success = open_parts_price_list_report()
            if report_success:
                # Configure report parameters
                params = PartsPriceListParams(
                    from_department='130',
                    from_franchise='TOY',
                    output_file_name='Parts Price List Report - 130.csv'
                )
                # Download the report
                download_success = parts_price_list_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Parts Price List Report")
                    close_tune_application()
                    return False
                logger.info("Parts Price List Report generated successfully")
            else:
                logger.error("Failed to open Parts Price List Report")
                close_tune_application()
                return False
            
            # Generate Parts by Bin Location Report
            logger.info("Generating Parts by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                # Configure report parameters
                params = PartsByBinLocationParams(
                    from_department='130',
                    from_franchise='TOY',
                    show_stock_as='Available Stock',
                    print_when_stock_not_zero=True,
                    output_file_name='Parts by Bin Location Report - 130.csv'
                )
                # Download the report
                download_success = parts_by_bin_location_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Parts by Bin Location Report")
                    close_tune_application()
                    return False
                logger.info("Parts by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Parts by Bin Location Report")
                close_tune_application()
                return False
            
            # Select 145 Department - MCT Tyres
            for i in range(5): # Go to department menu
                pyautogui.hotkey('shift', 'tab')
                time.sleep(0.1)
            for i in range(3): # Select 145
                pyautogui.press('down')
                time.sleep(0.1)

            # Move to menu
            for i in range(5):
                pyautogui.press('tab')

            # Generate Tyres Price List Report
            logger.info("Generating Tyres Price List Report...")
            report_success = open_parts_price_list_report(currently_selected_report='Parts By Bin Location')
            if report_success:
                # Configure report parameters
                params = PartsPriceListParams(
                    from_department='145',
                    from_franchise='TOY',
                    output_file_name='Parts Price List Report - 145.csv'
                )
                # Download the report
                download_success = parts_price_list_report_download(params, reports_dir=reports_dir)
                if not download_success:    
                    logger.error("Failed to download Tyres Price List Report")
                    close_tune_application()
                    return False
                logger.info("Tyres Price List Report generated successfully")
            else:
                logger.error("Failed to open Tyres Price List Report")
                close_tune_application()
                return False
            
            # Generate Tyres by Bin Location Report
            logger.info("Generating Tyres by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                # Configure report parameters
                params = PartsByBinLocationParams(
                    from_department='145',
                    from_franchise='TOY',
                    output_file_name='Parts by Bin Location Report - 145.csv'
                )
                # Download the report
                download_success = parts_by_bin_location_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Tyres by Bin Location Report")
                    close_tune_application()
                    return False
                logger.info("Tyres by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Tyres by Bin Location Report")
                close_tune_application()
                return False
            
            # Select 330 Department - Ingham Toyota
            for i in range(5): # Go to department menu
                pyautogui.hotkey('shift', 'tab')
                time.sleep(0.1)
            for i in range(7): # Select 330
                pyautogui.press('down')
                time.sleep(0.1)

            # Move to menu
            for i in range(5):
                pyautogui.press('tab')

            # Generate Ingham Toyota Parts Price List Report
            logger.info("Generating Ingham Toyota Parts Price List Report...")
            report_success = open_parts_price_list_report(currently_selected_report='Parts By Bin Location')
            if report_success:
                # Configure report parameters
                params = PartsPriceListParams(
                    from_department='330',
                    from_franchise='TOY',
                    output_file_name='Parts Price List Report - 330.csv'
                )
                # Download the report
                download_success = parts_price_list_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Ingham Toyota Parts Price List Report")
                    close_tune_application()
                    return False
                logger.info("Ingham Toyota Parts Price List Report generated successfully")
            else:
                logger.error("Failed to open Ingham Toyota Parts Price List Report")
                close_tune_application()
                return False
            
            # Generate Ingham Toyota Parts by Bin Location Report
            logger.info("Generating Ingham Toyota Parts by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                # Configure report parameters
                params = PartsByBinLocationParams(
                    from_department='330',
                    from_franchise='TOY',
                    output_file_name='Parts by Bin Location Report - 330.csv'
                )
                # Download the report
                download_success = parts_by_bin_location_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Ingham Toyota Parts by Bin Location Report")
                    close_tune_application()
                    return False
                logger.info("Ingham Toyota Parts by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Ingham Toyota Parts by Bin Location Report")
                close_tune_application()

            # Select Company 04 - Charters Towers Partnership
            for i in range(7): # Go to company menu
                pyautogui.hotkey('shift', 'tab')
            pyautogui.press('down')
            logger.info("Selected Company 04 - Charters Towers Partnership")
            time.sleep(2) # Wait for 'Updating' to finish
            # Department 430 - Parts & Acc selected by default

            # Move to menu
            for i in range(7):
                pyautogui.press('tab')
            
            # Generate Charters Towers Partnership Parts Price List Report
            logger.info("Generating Charters Towers Partnership Parts Price List Report...")
            report_success = open_parts_price_list_report()
            if report_success:
                # Configure report parameters
                params = PartsPriceListParams(
                    from_department='430',
                    from_franchise='TOY',
                    output_file_name='Parts Price List Report - 430.csv'
                )
                # Download the report
                download_success = parts_price_list_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Charters Towers Partnership Parts Price List Report")
                    close_tune_application()
                    return False
                logger.info("Charters Towers Partnership Parts Price List Report generated successfully")
            else:
                logger.error("Failed to open Charters Towers Partnership Parts Price List Report")
                close_tune_application()
                return False

            # Generate Charters Towers Partnership Parts by Bin Location Report

            logger.info("Generating Charters Towers Partnership Parts by Bin Location Report...")
            report_success = open_parts_by_bin_location_report()
            if report_success:
                # Configure report parameters
                params = PartsByBinLocationParams(
                    from_department='430',
                    from_franchise='TOY',
                    output_file_name='Parts by Bin Location Report - 430.csv'
                )
                # Download the report
                download_success = parts_by_bin_location_report_download(params, reports_dir=reports_dir)
                if not download_success:
                    logger.error("Failed to download Charters Towers Partnership Parts by Bin Location Report")
                    close_tune_application()
                    return False
                logger.info("Charters Towers Partnership Parts by Bin Location Report generated successfully")
            else:
                logger.error("Failed to open Charters Towers Partnership Parts by Bin Location Report")
                close_tune_application()
                return False
            
            # Close TUNE
            close_tune_application()
            logger.info("TUNE reports generation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during TUNE report generation: {e}")
            traceback.print_exc()
            # Try to close TUNE if it's open
            try:
                close_tune_application()
            except:
                pass
            return False

def main(config: TuneConfig) -> bool:
    """Main entry point: run TUNE report generation with the given config."""
    global _config
    _config = config
    try:
        config.validate()
        images_dir = config.images_dir or _get_images_dir()
        login_image = os.path.join(images_dir, 'tune_login_screen.png')
        app_image = os.path.join(images_dir, 'tune_application_screen.png')
        missing_images = []
        if not os.path.exists(login_image):
            missing_images.append('tune_login_screen.png')
        if not os.path.exists(app_image):
            missing_images.append('tune_application_screen.png')
        if missing_images:
            missing_str = ', '.join(missing_images)
            logger.error(f"Missing reference images: {missing_str}")
            return False
        report_generator = TuneReportGenerator(config)
        return report_generator.run_reports()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    finally:
        _config = None


if __name__ == "__main__":
    config = TuneConfig.from_env()
    success = main(config)
    sys.exit(0 if success else 1) 