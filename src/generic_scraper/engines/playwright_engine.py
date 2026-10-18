from __future__ import annotations

from typing import Callable

from generic_scraper.config import ScraperType
from generic_scraper.engines import register_engine
from generic_scraper.errors import EngineUnavailableError

_SUPPORTED_BROWSERS = ("chrome", "firefox")


def _default_browser_launcher(browser_type: str | None) -> None:
    """Real launcher used in production; lazily imports playwright."""
    from playwright.sync_api import sync_playwright  # noqa: F401

    raise NotImplementedError(
        "Real playwright browser launching is not implemented yet."
    )


def _default_availability_check() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


class PlaywrightEngine:
    """Engine backed by Playwright-driven browsers."""

    def __init__(
        self,
        config: ScraperType,
        browser_launcher: Callable[[str | None], None] | None = None,
        availability_check: Callable[[], bool] | None = None,
    ):
        self.config = config
        self.browser_type = config.browser_type
        self._browser_launcher = (
            browser_launcher if browser_launcher is not None else _default_browser_launcher
        )
        self._availability_check = (
            availability_check if availability_check is not None else _default_availability_check
        )

    def is_available(self) -> bool:
        """Return True if Playwright is importable/usable (or per injected check)."""
        return self._availability_check()

    def start(self) -> None:
        """Launch the configured browser via `browser_launcher`.

        Raises:
            EngineUnavailableError: if `browser_type` is not one of "chrome"/"firefox".
        """
        if self.config.browser_type not in _SUPPORTED_BROWSERS:
            raise EngineUnavailableError(
                f"Unsupported browser_type: {self.config.browser_type!r}"
            )
        self._browser_launcher(self.config.browser_type)

    def fetch(self, url: str) -> str:
        """Fetch `url` and return the raw HTML."""
        raise NotImplementedError("PlaywrightEngine.fetch is not implemented yet.")


register_engine("playwright", PlaywrightEngine)
