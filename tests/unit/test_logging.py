import logging

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.playwright_engine import PlaywrightEngine
from generic_scraper.engines.requests_engine import RequestsEngine
from generic_scraper.scraper import Scraper


def test_scraper_logs_engine_choice_on_init(caplog):
    with caplog.at_level(logging.INFO, logger="generic_scraper"):
        Scraper(ScraperType())
    assert any("requests" in r.message for r in caplog.records)


def test_scraper_logs_fallback(caplog, monkeypatch):
    monkeypatch.setattr(PlaywrightEngine, "is_available", lambda self: False)
    with caplog.at_level(logging.WARNING, logger="generic_scraper"):
        Scraper(ScraperType(scraper_engine="playwright"))
    assert any("fallback" in r.message.lower() for r in caplog.records)


def test_scraper_logs_retry_attempt(caplog, monkeypatch):
    calls = {"n": 0}

    def flaky_fetch(self, url):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("boom")
        return "<html><title>Recovered</title></html>"

    monkeypatch.setattr(RequestsEngine, "fetch", flaky_fetch)
    scraper = Scraper(ScraperType(retry_attempts=3))
    with caplog.at_level(logging.WARNING, logger="generic_scraper"):
        scraper.fetch("https://example.com")
    assert any("retry" in r.message.lower() for r in caplog.records)


def test_scraper_logs_successful_fetch(caplog, monkeypatch):
    monkeypatch.setattr(
        RequestsEngine, "fetch", lambda self, url: "<html><title>Example</title></html>"
    )
    scraper = Scraper(ScraperType())
    with caplog.at_level(logging.INFO, logger="generic_scraper"):
        scraper.fetch("https://example.com/test-page")
    records = [r for r in caplog.records if "https://example.com/test-page" in r.message]
    assert any("beautifulsoup" in r.message for r in records)
