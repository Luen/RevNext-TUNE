"""
Reset TUNE (if already open) or launch and login, then open Parts -> Sales -> Work With Orders.
Run from repo root with tune_dms installed: pip install -e packages/tune_dms

  python scripts/run_tune_work_with_orders.py

Requires TUNE_USER_ID and TUNE_USER_PASSWORD in env (or .env) for the launch+login path.
"""
import logging
import sys
import time

import pyautogui

from tune_dms.config import TuneConfig
from tune_dms import state
from tune_dms import screen
from tune_dms import app
from tune_dms.parts.sales import WorkWithOrderParams, fill_add_order_form

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def ensure_menu_at_top(max_attempts: int = 100) -> bool:
    """Press Up until tune_menu_selected.png is found (menu first item selected)."""
    for attempt in range(max_attempts):
        if screen.find_image_immediate("tune_menu_selected.png"):
            return True
        pyautogui.press("up")
        time.sleep(0.03)
    logger.warning("tune_menu_selected.png not found after %d attempts", max_attempts)
    return False


def main() -> bool:
    try:
        config = TuneConfig.from_env()
        config.validate()
        state._config = config
    except ValueError as e:
        logger.error("Config invalid (need TUNE_USER_ID and TUNE_USER_PASSWORD): %s", e)
        return False

    try:
        logger.info("Trying to reset TUNE (if already open)...")
        reset_ok = app.reset_tune_to_startup()
        if reset_ok:
            logger.info("TUNE was open; reset to startup.")
        else:
            logger.info("TUNE not in focus or reset failed; launching and logging in...")
            app.launch_tune_application()
            time.sleep(3)
            if not app.login_to_tune():
                logger.error("Login failed.")
                return False
        time.sleep(1)

        logger.info("Ensuring menu is at top...")
        if not ensure_menu_at_top():
            logger.warning("Menu may not be at top; continuing anyway.")
        time.sleep(0.2)

        if not app.open_work_with_orders():
            logger.error("Failed to open Work With Orders.")
            return False

        time.sleep(0.5)
        # Fill Add Order form with dummy data
        dummy_order = WorkWithOrderParams(
            customer_id="166275",  # Shopify payment method
            sales_rep=None,
            order_type=None,
            phone="0415947748",
            contact="Luen Warneke",
            email="warnekeluen@gmail.com",
            date_reqd="06/02/2026",
            order_note="Order Note",
            email_2="warnekeluen@gmail.com",
            fax=None,
            mobile="0415947748",
            contact_2="Luen Warneke",
            state="QLD",
            postal_code="4810",
            address_line_4=None,
            address_line_3=None,
            address_line_2="Garbutt",
            address_line_1="123 Duckworth St",
            address_unknown=False,
            ship_to="Luen Warneke",
            ship_via_index=0,
            tax_type_index=0,
            customer_po="#1000",
        )
        if not fill_add_order_form(dummy_order):
            logger.error("Failed to fill Add Order form.")
            return False

        logger.info("Done. Work With Orders opened and dummy order form submitted.")
        return True
    except Exception as e:
        logger.exception("Error: %s", e)
        return False
    finally:
        state._config = None


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
