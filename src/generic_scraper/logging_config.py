"""Logging setup for the generic_scraper package.

Scraper logs through the ``"generic_scraper"`` named logger at the module
level; this module provides a convenience configurator for applications/CLIs
that want a sensible default stream handler. Library code never calls this
implicitly -- it only ever does ``logging.getLogger("generic_scraper")`` and
emits records, leaving handler/level configuration to the application.
"""
from __future__ import annotations

import logging

LOGGER_NAME = "generic_scraper"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the ``generic_scraper`` logger with a stream handler.

    Idempotent: calling this repeatedly will not duplicate handlers.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
