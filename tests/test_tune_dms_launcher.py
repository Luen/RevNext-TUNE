"""Tests for tune_dms launcher and refactored modules (imports and validation). No GUI."""

from tune_dms.config import TuneConfig
from tune_dms.launcher import main, TuneReportGenerator
from tune_dms.launcher import (
    PartsPriceListParams,
    PartsByBinLocationParams,
    parts_price_list_report_download,
    parts_by_bin_location_report_download,
)
from tune_dms import state
from tune_dms import screen
from tune_dms import app
from tune_dms.parts.reports import (
    open_parts_price_list_report,
    open_parts_by_bin_location_report,
)


class TestLauncherImports:
    """Smoke tests: refactored modules and launcher import correctly."""

    def test_launcher_main_and_generator_import(self):
        assert callable(main)
        assert TuneReportGenerator is not None

    def test_parts_reports_params_import(self):
        assert PartsPriceListParams is not None
        assert PartsByBinLocationParams is not None

    def test_state_screen_app_import(self):
        assert state._config is None
        assert hasattr(screen, "waitFor")
        assert hasattr(screen, "find_image_immediate")
        assert hasattr(screen, "get_images_dir")
        assert hasattr(app, "launch_tune_application")
        assert hasattr(app, "login_to_tune")
        assert hasattr(app, "close_tune_application")
        assert hasattr(app, "reset_tune_to_startup")

    def test_parts_reports_functions_import(self):
        assert callable(open_parts_price_list_report)
        assert callable(open_parts_by_bin_location_report)
        assert callable(parts_price_list_report_download)
        assert callable(parts_by_bin_location_report_download)


class TestLauncherMain:
    """main() fails fast on invalid config (no GUI started)."""

    def test_main_returns_false_when_config_invalid(self):
        config = TuneConfig(user_id="", password="")
        result = main(config)
        assert result is False

    def test_tune_report_generator_instantiates(self):
        config = TuneConfig(user_id="u", password="p")
        gen = TuneReportGenerator(config)
        assert gen.config is config
