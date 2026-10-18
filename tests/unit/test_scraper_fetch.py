import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.requests_engine import RequestsEngine
from generic_scraper.scraper import Scraper


def test_fetch_returns_parsed_document_with_title(monkeypatch):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>Example</title></html>")
    scraper = Scraper(ScraperType())
    doc = scraper.fetch("https://example.com/test-page")
    assert doc.title == "Example"


def test_fetch_retries_transient_errors_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def flaky_fetch(self, url):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("boom")
        return "<html><title>Recovered</title></html>"

    monkeypatch.setattr(RequestsEngine, "fetch", flaky_fetch)
    scraper = Scraper(ScraperType(retry_attempts=3))
    doc = scraper.fetch("https://example.com")
    assert doc.title == "Recovered"
    assert calls["n"] == 2


def test_fetch_gives_up_after_retry_attempts_exhausted(monkeypatch):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: (_ for _ in ()).throw(ConnectionError("boom")))
    scraper = Scraper(ScraperType(retry_attempts=3))
    with pytest.raises(ConnectionError):
        scraper.fetch("https://example.com")
