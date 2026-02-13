"""
Custom logger support for tune_dms. Consumers can inject their own logger so all
library log output goes to their handler/format.

Example:
    import logging
    from tune_dms import set_logger

    my_logger = logging.getLogger("my_app.tune")
    my_logger.setLevel(logging.DEBUG)
    set_logger(my_logger)
"""

import logging
from typing import Optional

_custom_logger: Optional[logging.Logger] = None


def set_logger(logger: Optional[logging.Logger]) -> None:
    """Set a custom logger for the package. Pass None to use the default loggers again."""
    global _custom_logger
    _custom_logger = logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """Return the custom logger if set, otherwise the standard logger for the given module."""
    if _custom_logger is not None:
        return _custom_logger
    return logging.getLogger(module_name if module_name else "tune_dms")


class _LoggerProxy:
    """Proxy that forwards to get_logger(module_name) on each call so a custom logger can be set after import."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def _logger(self) -> logging.Logger:
        return get_logger(self._name)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._logger().debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._logger().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._logger().warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._logger().error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._logger().exception(msg, *args, **kwargs)


def logger_proxy(module_name: str) -> _LoggerProxy:
    """Return a logger proxy for the given module name. Use in each module: logger = logger_proxy(__name__)."""
    return _LoggerProxy(module_name)
