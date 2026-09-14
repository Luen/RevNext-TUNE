"""
Custom logger support for revnext. Consumers can inject their own logger so all
library log output goes to their handler/format.

Example:
    import logging
    from revnext import set_logger

    my_logger = logging.getLogger("my_app.revnext")
    my_logger.setLevel(logging.DEBUG)
    set_logger(my_logger)
"""

import logging

_custom_logger: logging.Logger | None = None


def set_logger(logger: logging.Logger | None) -> None:
    """Set a custom logger for the package. Pass None to use the default logger again."""
    global _custom_logger
    _custom_logger = logger


def get_logger(module_name: str | None = None) -> logging.Logger:
    """Return the custom logger if set, otherwise the standard logger for the given module."""
    if _custom_logger is not None:
        return _custom_logger
    return logging.getLogger(module_name if module_name else "revnext")
