from __future__ import annotations

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.playwright_engine import PlaywrightEngine
from generic_scraper.engines.selenium_engine import SeleniumEngine


@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
def test_engine_launches_configured_browser(engine_cls, browser):
    cfg = ScraperType(browser_type=browser)
    launches = []
    engine = engine_cls(cfg, browser_launcher=launches.append, availability_check=lambda: True)
    engine.start()
    assert launches == [browser]


@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
def test_engine_unavailable_when_check_fails(engine_cls):
    engine = engine_cls(ScraperType(browser_type="chrome"), availability_check=lambda: False)
    assert engine.is_available() is False


@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
def test_engine_available_when_check_passes(engine_cls):
    engine = engine_cls(ScraperType(browser_type="chrome"), availability_check=lambda: True)
    assert engine.is_available() is True


@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
def test_start_raises_for_unsupported_browser_type(engine_cls):
    from generic_scraper.errors import EngineUnavailableError

    engine = engine_cls(
        ScraperType(browser_type="ie6"),
        browser_launcher=lambda b: None,
        availability_check=lambda: True,
    )
    with pytest.raises(EngineUnavailableError):
        engine.start()


def test_default_availability_check_does_not_import_at_module_level():
    # Importing the modules must not require playwright/selenium to be installed.
    import generic_scraper.engines.playwright_engine  # noqa: F401
    import generic_scraper.engines.selenium_engine  # noqa: F401
