from __future__ import annotations

from generic_scraper.engines.base import Engine
from generic_scraper.errors import UnsupportedScraperEngineError

__all__ = ["Engine", "register_engine", "get_engine_class"]

_REGISTRY: dict[str, type[Engine]] = {}


def register_engine(name: str, cls: type[Engine]) -> None:
    """Register an engine class under `name` in the module-level registry."""
    _REGISTRY[name] = cls


def get_engine_class(name: str) -> type[Engine]:
    """Look up a registered engine class by name.

    Raises:
        UnsupportedScraperEngineError: if `name` is not registered.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise UnsupportedScraperEngineError(name) from None


# Import built-in engines so they self-register at package import time.
from generic_scraper.engines import requests_engine  # noqa: E402,F401
from generic_scraper.engines import playwright_engine, selenium_engine  # noqa: E402,F401
