"""
TUNE application lifecycle: launch, login, close, reset. Uses screen helpers and state._config.
"""

import os
import time
import logging
import subprocess
from typing import Optional

import pyautogui

from tune_dms import state
from tune_dms import screen

logger = logging.getLogger(__name__)


def launch_tune_application():
    """Launch the TUNE software application using the shortcut (path from config)."""
    if not state._config:
        raise RuntimeError("TUNE config not set. Call run_tune_reports(config) first.")
    logger.info("Launching TUNE software using shortcut...")
    shortcut_path = state._config.shortcut_path
    try:
        if not os.path.exists(shortcut_path):
            logger.error(f"TUNE shortcut not found at {shortcut_path}")
            raise FileNotFoundError(f"TUNE shortcut not found at {shortcut_path}")

        process = subprocess.Popen(f'start "" "{shortcut_path}"', shell=True)
        logger.info("TUNE process started using shortcut")
        return process
    except Exception as e:
        logger.error(f"Failed to launch TUNE: {e}")
        raise


def login_to_tune():
    """Login to TUNE using credentials from config (set by run_tune_reports)."""
    if not state._config:
        raise RuntimeError("TUNE config not set. Call run_tune_reports(config) first.")
    logger.info("Attempting to login to TUNE...")
    login_screen = screen.waitFor("tune_login_screen.png")
    if not login_screen:
        logger.error("Login screen not found")
        return False
    pyautogui.click(pyautogui.center(login_screen))
    time.sleep(0.5)
    if screen.waitFor("tune_login_screen_environment.png", timeout=1):
        logger.info("TUNE Environment not selected, selecting")
        time.sleep(0.2)
        pyautogui.press("e")
        time.sleep(0.2)
        pyautogui.press("down")
        time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.5)
    pyautogui.write(state._config.user_id)
    logger.info("Entered User ID")
    time.sleep(0.5)
    pyautogui.press("tab")
    time.sleep(0.5)
    pyautogui.write(state._config.password)
    logger.info("Entered Password")
    time.sleep(0.5)

    pyautogui.press("enter")
    logger.info("Submitted login form")

    login_error = screen.waitFor("tune_login_error.png", timeout=3)
    if login_error:
        logger.error("Login failed")
        time.sleep(2)
        pyautogui.press("space")
        return False

    app_screen = screen.waitFor(
        "tune_application_screen.png", timeout=30
    )
    if not app_screen:
        logger.error("Application screen not found after login")
        return False

    logger.info("Successfully logged into TUNE")
    return True


def close_tune_application():
    """Close TUNE application using Alt, Down, E keyboard shortcut."""
    try:
        logger.info("Attempting to close TUNE application...")
        pyautogui.press("alt")
        time.sleep(0.3)
        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("e")
        logger.info("TUNE close sequence executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error while closing TUNE: {e}")
        return False


def reset_tune_to_startup(
    department_index: Optional[int] = None,
    division_index: Optional[int] = None,
    company_index: Optional[int] = None,
) -> bool:
    """
    Reset TUNE to normal startup state when it is already open and in focus.
    Moves to top (Menu), clears search, then optionally sets department/division/company by index.
    """
    position = screen.find_image_immediate("tune_application_screen.png")
    if not position:
        return False
    logger.info("TUNE window found and in focus")
    center = pyautogui.center(position)
    pyautogui.click(center[0] + 50, center[1] + 150)
    time.sleep(0.3)
    logger.info("Attempting to reset menu")
    max_attempts = 100
    attempts = 0
    while not screen.find_image_immediate("tune_menu_selected.png") and attempts < max_attempts:
        pyautogui.press("up")
        time.sleep(0.03)
        attempts += 1
    if attempts >= max_attempts:
        logger.warning("tune_menu_selected.png not found after %d attempts", max_attempts)
    time.sleep(0.2)
    logger.info("Attempting to clear search")
    for _ in range(3):
        pyautogui.hotkey("shift", "tab")
        time.sleep(0.1)
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.2)
    logger.info("Attempting to select department")
    for _ in range(5):
        pyautogui.hotkey("shift", "tab")
        time.sleep(0.1)
    if department_index is not None:
        for _ in range(department_index):
            pyautogui.press("down")
            time.sleep(0.05)
    pyautogui.hotkey("shift", "tab")
    time.sleep(0.1)
    logger.info("Attempting to select division")
    if division_index is not None:
        for _ in range(division_index):
            pyautogui.press("down")
            time.sleep(0.05)
    pyautogui.hotkey("shift", "tab")
    time.sleep(0.1)
    logger.info("Attempting to select company")
    if company_index is not None:
        for _ in range(company_index):
            pyautogui.press("down")
            time.sleep(0.05)
    logger.info("Going back to menu")
    for _ in range(7):
            pyautogui.press("tab")
            time.sleep(0.05)
    logger.info("TUNE reset to normal startup config")
    return True
