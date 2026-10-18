import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.playwright_engine import PlaywrightEngine
from generic_scraper.engines.selenium_engine import SeleniumEngine
from generic_scraper.errors import EngineUnavailableError, UnsupportedScraperEngineError
from generic_scraper.scraper import Scraper


def test_scraper_uses_requests_engine_by_default():
    scraper = Scraper(ScraperType.empty())
    assert scraper.engine_name == "requests"


def test_scraper_raises_for_unsupported_engine():
    with pytest.raises(UnsupportedScraperEngineError):
        Scraper(ScraperType(scraper_engine="unknown"))


def test_scraper_falls_back_to_requests_when_primary_unavailable(monkeypatch):
    # monkeypatch PlaywrightEngine.is_available to return False
    monkeypatch.setattr(PlaywrightEngine, "is_available", lambda self: False)
    scraper = Scraper(ScraperType(scraper_engine="playwright"))
    assert scraper.engine_name == "requests"


def test_scraper_falls_back_to_configured_secondary(monkeypatch):
    monkeypatch.setattr(
        SeleniumEngine,
        "start",
        lambda self: (_ for _ in ()).throw(EngineUnavailableError("selenium")),
    )
    scraper = Scraper(ScraperType(scraper_engine="selenium", secondary="requests"))
    assert scraper.engine_name == "requests"
