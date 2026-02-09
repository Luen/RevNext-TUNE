"""
Screen/image helpers: wait for images, find image once. Used by app and report modules.
"""

import os
import time
import logging

import pyautogui

from tune_dms import state

logger = logging.getLogger(__name__)


def _get_images_dir() -> str:
    """Return the images directory from config or package default (tune_dms/images/)."""
    if state._config and state._config.images_dir:
        return state._config.images_dir
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pkg_dir, "images")


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


def find_image_immediate(image_name: str, confidence: float = 0.9):
    """
    Try to find an image on screen once (no wait). Use to check if a window is already visible.

    Returns:
        Box (left, top, width, height) if found, None otherwise.
    """
    image_path = os.path.join(_get_images_dir(), image_name)
    if not os.path.exists(image_path):
        return None
    try:
        return pyautogui.locateOnScreen(image_path, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        logger.debug(f"find_image_immediate {image_name}: {e}")
        return None


def wait_for_image_to_disappear(
    image_name: str,
    timeout: float = 30,
    confidence: float = 0.9,
    poll_interval: float = 0.3,
) -> bool:
    """
    Wait for an image to no longer be visible on screen (e.g. after validation finishes).

    Returns:
        True if the image disappeared within the timeout, False if still visible when timeout is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not find_image_immediate(image_name, confidence=confidence):
            return True
        time.sleep(poll_interval)
    logger.warning("Image %s still visible after %.1f seconds", image_name, timeout)
    return False


def get_images_dir() -> str:
    """Return the images directory (for launcher validation)."""
    return _get_images_dir()
