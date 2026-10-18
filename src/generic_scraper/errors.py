"""Error hierarchy for the generic_scraper package."""


class ScraperError(Exception):
    """Base class for all generic_scraper errors."""


class UnsupportedScraperEngineError(ScraperError):
    """Raised when a requested scraper engine is not supported."""

    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        super().__init__(f"Unsupported scraper engine: {engine_name!r}")


class EngineUnavailableError(ScraperError):
    """Raised when an engine fails its capability check or fails to start."""


class EngineStartError(EngineUnavailableError):
    """Raised when an engine fails to start on the worker."""
