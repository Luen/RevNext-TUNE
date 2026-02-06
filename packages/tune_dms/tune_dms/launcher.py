"""
TUNE DMS launcher: entry point. Delegates report run to utils.TuneReportGenerator.
Re-exports report params and download functions for package API.
"""

import os
import logging
import sys

from tune_dms.config import TuneConfig
from tune_dms import state
from tune_dms import screen
from tune_dms.utils import TuneReportGenerator
from tune_dms.parts.reports import (
    PartsPriceListParams,
    PartsByBinLocationParams,
    parts_price_list_report_download,
    parts_by_bin_location_report_download,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main(config: TuneConfig) -> bool:
    """Main entry point: run TUNE report generation with the given config."""
    try:
        config.validate()
        state._config = config
        images_dir = config.images_dir or screen.get_images_dir()
        login_image = os.path.join(images_dir, "tune_login_screen.png")
        app_image = os.path.join(images_dir, "tune_application_screen.png")
        missing_images = []
        if not os.path.exists(login_image):
            missing_images.append("tune_login_screen.png")
        if not os.path.exists(app_image):
            missing_images.append("tune_application_screen.png")
        if missing_images:
            missing_str = ", ".join(missing_images)
            logger.error(f"Missing reference images: {missing_str}")
            return False
        report_generator = TuneReportGenerator(config)
        return report_generator.run_reports()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    finally:
        state._config = None


if __name__ == "__main__":
    config = TuneConfig.from_env()
    success = main(config)
    sys.exit(0 if success else 1)
