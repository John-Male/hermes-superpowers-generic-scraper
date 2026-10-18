"""Step definitions for `features/03_defaults_and_fallbacks.feature`.

These steps cover default-value behavior (no engine/browser configured) and
fallback behavior when a configured engine is unavailable at Scraper
init-time.

The "<engine> is not available" step forces unavailability for exactly one
scenario by monkeypatching that engine class's `is_available` method via
`unittest.mock.patch.object(...).start()` and registering the matching
`.stop()` with `context.add_cleanup(...)`. This is required because
`features/environment.py`'s `before_all`/`after_all` hooks only save/restore
the module-level launcher/availability hooks *once* for the whole suite --
an ad hoc override here without `context.add_cleanup` would leak into every
later scenario (including feature 01/02's scenarios, which expect
playwright/selenium to succeed by default).
"""

from __future__ import annotations

from unittest.mock import patch

from behave import given, then

from generic_scraper.engines.playwright_engine import PlaywrightEngine
from generic_scraper.engines.selenium_engine import SeleniumEngine

_ENGINE_CLASSES = {
    "playwright": PlaywrightEngine,
    "selenium": SeleniumEngine,
}


@given('"{engine}" is not available on the worker node')
def step_engine_not_available(context, engine):
    engine_class = _ENGINE_CLASSES[engine]
    patcher = patch.object(engine_class, "is_available", lambda self: False)
    patcher.start()
    context.add_cleanup(patcher.stop)


@then('the Scraper should use "{engine}" as the default scraper engine')
def step_scraper_default_engine(context, engine):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.engine_name == engine, (
        f"Expected default engine {engine!r}, got {context.scraper.engine_name!r}"
    )


@then("the Scraper should have no browser configured")
def step_scraper_no_browser(context):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.config.browser_type is None, (
        f"Expected no browser configured, got "
        f"{context.scraper.config.browser_type!r}"
    )


@then('the Scraper should fall back to "{engine}"')
def step_scraper_falls_back(context, engine):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.engine_name == engine, (
        f"Expected fallback engine {engine!r}, got {context.scraper.engine_name!r}"
    )
