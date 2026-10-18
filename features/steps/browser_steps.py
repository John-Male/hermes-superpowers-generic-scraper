"""Step definitions for `features/02_browser_configuration.feature`.

No extra mocking seam is wired up here: `features/environment.py`'s
`before_all`/`after_all` already globally monkeypatch the Playwright/Selenium
engines' `_default_browser_launcher`/`_default_availability_check` hooks
(Task 7's injectable seams) to always succeed, for the whole test run. That
means a `Scraper` built by the existing `common_steps.py` "When I initialize
the Scraper..." step with an explicit `browser_type` already ends up with a
real (non-fallback) `engine_name` of "playwright"/"selenium" with no browser
actually launched -- so this step only needs to assert on the resulting
`Scraper` state, not construct anything itself.
"""

from __future__ import annotations

from behave import then


@then('the Scraper should launch "{browser}" for "{engine}"')
def step_scraper_launches_browser(context, browser, engine):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.config.browser_type == browser, (
        f"Expected browser_type {browser!r}, got "
        f"{context.scraper.config.browser_type!r}"
    )
    assert context.scraper.engine_name == engine, (
        f"Expected engine {engine!r}, got {context.scraper.engine_name!r}"
    )
