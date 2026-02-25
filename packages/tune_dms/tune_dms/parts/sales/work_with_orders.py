"""
Work With Orders: fill the Add Order form to create pickslips/orders in TUNE.
Assumes Parts -> Sales -> Work With Orders is already open.
"""

import time
from dataclasses import dataclass
from typing import Literal, Optional

import pyautogui

from tune_dms import screen

from tune_dms.logger import logger_proxy

logger = logger_proxy(__name__)

FREIGHT_TERMS = ("Per Order", "Per Invoice", "Per Day", "Per P/O")
BACKORDER_ACTIONS = ("Normal B/O", "Cancel B/O", "Hold B/O")


def _normalize_phone(phone: Optional[str]) -> str:
    """Strip spaces and substitute +61 with 0."""
    if not phone or not phone.strip():
        return ""
    s = phone.strip().replace(" ", "")
    if s.startswith("+61"):
        s = "0" + s[3:]
    return s


def _normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Return 6 digits DDMMYY (slashes removed, year two digits). Returns None if empty."""
    if not date_str or not str(date_str).strip():
        return None
    s = str(date_str).strip()
    if "/" in s:
        parts = [p.strip() for p in s.split("/") if p.strip()]
        if len(parts) >= 3:
            day, month, year = parts[0], parts[1], parts[2]
            year = year[-2:] if len(year) >= 2 else year.zfill(2)
            return day.zfill(2) + month.zfill(2) + year.zfill(2)
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 6:
        return digits
    if len(digits) == 8:
        return digits[:2] + digits[2:4] + digits[6:8]
    return digits[:6].zfill(6) if digits else None


def _type_field(value: Optional[str], delay: float = 0.05) -> None:
    """Type value if present."""
    if value is not None and str(value).strip():
        pyautogui.write(str(value).strip())
    time.sleep(delay)


def _shift_tab(times: int = 1, delay: float = 0.05) -> None:
    for _ in range(times):
        pyautogui.hotkey("shift", "tab")
        time.sleep(delay)


def _tab(times: int = 1, delay: float = 0.05) -> None:
    """Forward tab (no shift)."""
    for _ in range(times):
        pyautogui.press("tab")
        time.sleep(delay)


@dataclass
class WorkWithOrderParams:
    """Parameters for the Add Order form in Work With Orders."""

    # Payment method Customer ID
    customer_id: str
    sales_rep: Optional[str] = None  # Blank for default (logged-in user if Sales Rep role)
    # Dropdown: Order (default skip)
    order_type: Optional[str] = None  # e.g. "Order" or None to skip
    phone: Optional[str] = None  # Normalized: spaces stripped, +61 -> 0
    contact: Optional[str] = None
    email: Optional[str] = None
    date_reqd: Optional[str] = None
    order_note: Optional[str] = None
    email_2: Optional[str] = None  # Email again
    fax: Optional[str] = None
    mobile: Optional[str] = None
    contact_2: Optional[str] = None  # Contact again
    state: Optional[str] = None
    postal_code: Optional[str] = None
    address_line_4: Optional[str] = None
    address_line_3: Optional[str] = None
    address_line_2: Optional[str] = None
    address_line_1: Optional[str] = None
    address_unknown: bool = False  # Spacebar to check
    ship_to: Optional[str] = None
    # Not supported (dropdowns; would need Down/Up to select). Ignored in form.
    freight_terms: Optional[Literal["Per Order", "Per Invoice", "Per Day", "Per P/O"]] = None
    backorder_action: Optional[
        Literal["Normal B/O", "Cancel B/O", "Hold B/O"]
    ] = None
    ship_via_index: Optional[int] = None  # Press Down this many times in dropdown
    tax_type_index: Optional[int] = None  # Press Up this many times (GST 10%, Other Fee, GST Free Export)
    customer_po: Optional[str] = None  # e.g. Shopify order number
    prefilled_data: bool = False  # True if order has prefilled data (extra validation boxes; skip Address Validation)


def fill_add_order_form(params: WorkWithOrderParams) -> bool:
    """
    From the Work With Orders screen, press Add and fill the order form with the given params.
    Assumes Parts -> Sales -> Work With Orders is already open and focused.
    """
    try:
        # Tab 22, Enter (Add)
        for _ in range(22):
            pyautogui.press("tab")
            time.sleep(0.05)
        
        logger.info("Screen 1 Completed")
        pyautogui.press("enter")
        time.sleep(1)

        logger.info("Screen 2 Completed")
        # Enter again (next screen)
        pyautogui.press("enter")
        time.sleep(1)

        if params.prefilled_data:
            logger.info("Order has prefilled data")

        # Customer ID, Enter
        pyautogui.write(params.customer_id)
        time.sleep(0.05)
        pyautogui.press("enter")
        time.sleep(1)
        # SalesRep (or blank for default)
        _type_field(params.sales_rep)
        pyautogui.press("enter")
        time.sleep(0.1)

        # Rego Not Supported

        # Sub Type Not Supported

        _shift_tab(4)
        # Dropdown: Order (default skip)
        _type_field(params.order_type)
        _shift_tab(1)
        # Phone (normalize)
        _type_field(_normalize_phone(params.phone) if params.phone else None)
        _shift_tab(1)
        _type_field(params.contact)
        _shift_tab(1)
        _type_field(params.email)
        _shift_tab(1)
        time.sleep(1)

        if params.prefilled_data:
            logger.info("Prefilled data so traversing extra boxes")
            _shift_tab(2)
        
        # Validate Phone number
        if screen.find_image_immediate("tune_caution_validation_button_selected.png"):
            logger.warning("Caution validation dialog detected.")
            pyautogui.press("enter")
            
            time.sleep(1)
            screen.wait_for_image_to_disappear("tune_caution_validation_requesting.png")

        # If validation dialog errors, pause for user to fix then continue
        if screen.find_image_immediate("tune_error_validation_button.png"):
            logger.warning(
                "Error validation dialog detected. Please fix the error in TUNE manually, "
                "then press Enter in this terminal when ready to continue."
            )
            input("Press Enter in this terminal when ready to continue... ")
            pyautogui.click(screen.find_image_immediate("tune_favicon.png"))
            pyautogui.press("esc")
            time.sleep(5)
        
        # If phone is blank, then there's no need to validate phone number
        if params.phone:
            _shift_tab(1)
        
        time.sleep(1)
        _shift_tab(1)

        # Validate Email
        if screen.find_image_immediate("tune_caution_validation_button_selected.png"):
            logger.warning("Caution validation dialog detected.")
            pyautogui.press("enter")
            time.sleep(1)
            screen.wait_for_image_to_disappear("tune_caution_validation_requesting.png")

        # If validation dialog errors, pause for user to fix then continue
        if screen.find_image_immediate("tune_error_validation_button.png"):
            logger.warning(
                "Error validation dialog detected. Please fix the error in TUNE manually, "
                "then press Enter in this terminal when ready to continue."
            )
            input("Press Enter in this terminal when ready to continue... ")
            pyautogui.click(screen.find_image_immediate("tune_favicon.png"))
            pyautogui.press("esc")
            time.sleep(5)

        if params.phone:
            _shift_tab(2)
        if params.email:
            _shift_tab(1)

        if params.prefilled_data:
            logger.info("Prefilled data so skipping Address Validation checkbox")
            _shift_tab(1)

        # Shift + Tab to Date Reqd
        _type_field(_normalize_date(params.date_reqd))
        # Shift + Tab to Order Note
        _shift_tab(1)
        _type_field(params.order_note)
        _shift_tab(2)
        _type_field(params.email_2)
        _shift_tab(1)
        _type_field(params.fax)
        _shift_tab(1)
        _type_field(_normalize_phone(params.mobile) if params.mobile else None)

        # If validation dialog errors, pause for user to fix then continue
        if screen.find_image_immediate("tune_error_validation_button.png"):
            logger.warning(
                "Error validation dialog detected. Please fix the error in TUNE manually, "
                "then press Enter in this terminal when ready to continue."
            )
            input("Press Enter in this terminal when ready to continue... ")
            pyautogui.click(screen.find_image_immediate("tune_favicon.png"))
            pyautogui.press("esc")
            time.sleep(5)

        _shift_tab(3)
        _type_field(params.contact_2)
        _shift_tab(1)
        _type_field(params.state)
        _shift_tab(1)
        _type_field(params.postal_code)
        _shift_tab(1)
        _type_field(params.address_line_4)
        _shift_tab(1)
        _type_field(params.address_line_3)
        _shift_tab(1)
        _type_field(params.address_line_2)
        _shift_tab(1)
        _type_field(params.address_line_1)
        _shift_tab(1)
        # Address unknown checkbox
        if params.address_unknown:
            pyautogui.press("space")
        time.sleep(0.05)
        _shift_tab(1)
        _type_field(params.ship_to)
        # Freight Terms, Backorder Action: dropdowns, not supported — Tab past
        _shift_tab(3)
        # Ship via: press Down index times
        if params.ship_via_index is not None:
            for _ in range(params.ship_via_index):
                pyautogui.press("down")
                time.sleep(0.1)
        _shift_tab(1)
        # Tax Type: press Up index times
        if params.tax_type_index is not None:
            for _ in range(params.tax_type_index):
                pyautogui.press("up")
                time.sleep(0.1)
        _shift_tab(1)
        _type_field(params.customer_po)

        # Shift+Tab x 1, Enter (OK)
        _shift_tab(1)
        time.sleep(0.05)
        logger.info("Screen 3 Completed")
        # Input for user to confirm
        logger.info("Please check order details")
        input("Press Enter in this terminal when ready to continue... ")
        time.sleep(1)
        pyautogui.press("enter")

        
        logger.info("Please enter parts")
        input("Press Enter in this terminal when ready to continue... ")
        time.sleep(1)

        # Aways select the first part or specific franchise

        # When entering price, check for price below cost warning alert
        # When enter invaild price, check for error alert


        logger.info("Add Order form submitted")
        return True
    except Exception as e:
        logger.exception("Error filling Add Order form: %s", e)
        return False
