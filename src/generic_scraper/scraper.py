from __future__ import annotations

from generic_scraper.config import ScraperType
from generic_scraper.engines import Engine, get_engine_class
from generic_scraper.errors import EngineUnavailableError

_DEFAULT_FALLBACK_ENGINE = "requests"


class Scraper:
    """Orchestrates engine selection, construction, and fallback for a scrape."""

    def __init__(self, config: ScraperType):
        self.config = config

        engine_name = config.scraper_engine
        engine_class = get_engine_class(engine_name)  # propagates UnsupportedScraperEngineError
        engine = engine_class(config)

        try:
            if not engine.is_available():
                raise EngineUnavailableError(
                    f"Engine {engine_name!r} is not available"
                )
            engine.start()
        except EngineUnavailableError:
            fallback_name = self._determine_fallback(engine_name)
            fallback_class = get_engine_class(fallback_name)
            engine = fallback_class(config)
            engine.start()
            engine_name = fallback_name

        self.engine_name: str = engine_name
        self.engine: Engine = engine

    def _determine_fallback(self, primary_engine_name: str) -> str:
        """Determine which engine to fall back to when `primary_engine_name` fails.

        Falls back to `config.secondary` if set, else to the default fallback
        engine ("requests"), unless the primary already *was* the default
        fallback engine -- in that case there is no further fallback and the
        original error should propagate.
        """
        if primary_engine_name == _DEFAULT_FALLBACK_ENGINE:
            raise
        return self.config.secondary or _DEFAULT_FALLBACK_ENGINE
