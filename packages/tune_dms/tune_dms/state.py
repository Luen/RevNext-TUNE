"""
Runtime state for TUNE DMS launcher. Set by main() so screen and app modules
can access config without circular imports.
"""

from tune_dms.config import TuneConfig

# Set by launcher.main() before running; cleared in finally.
_config: TuneConfig | None = None
