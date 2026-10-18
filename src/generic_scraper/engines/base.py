from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Engine(Protocol):
    """Interface implemented by all scraper engines (requests/playwright/selenium)."""

    browser_type: str | None

    def is_available(self) -> bool:
        """Return True if this engine's runtime dependencies are usable."""
        ...

    def start(self) -> None:
        """Prepare the engine for fetching.

        Raises:
            EngineUnavailableError: if the engine cannot be used in this environment.
            EngineStartError: if startup fails (e.g. browser/driver fails to launch).
        """
        ...

    def fetch(self, url: str) -> str:
        """Fetch `url` and return the raw HTML."""
        ...
