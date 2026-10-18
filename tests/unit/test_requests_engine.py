from __future__ import annotations

from generic_scraper.config import ScraperType
from generic_scraper.engines.requests_engine import RequestsEngine


class FakeSession:
    def __init__(self, get_text: str = ""):
        self.proxies: dict = {}
        self.headers: dict = {}
        self._get_text = get_text

    def get(self, url):
        return FakeResponse(self._get_text)


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


def test_requests_engine_configures_proxy_on_session():
    cfg = ScraperType(use_proxy=True, proxy_url="http://proxy.example", proxy_port=8080)
    fake_session = FakeSession()
    engine = RequestsEngine(cfg, session=fake_session)
    engine.start()
    assert fake_session.proxies == {
        "http": "http://proxy.example:8080",
        "https": "http://proxy.example:8080",
    }


def test_requests_engine_sets_pass_key_header():
    cfg = ScraperType(proxy_pass_key="X-Proxy-Auth", proxy_pass_val="dummy-token-abc")
    fake_session = FakeSession()
    engine = RequestsEngine(cfg, session=fake_session)
    engine.start()
    assert fake_session.headers["X-Proxy-Auth"] == "dummy-token-abc"


def test_requests_engine_fetch_returns_response_text():
    fake_session = FakeSession(get_text="<html><title>t</title></html>")
    engine = RequestsEngine(ScraperType(), session=fake_session)
    engine.start()
    assert engine.fetch("https://example.com") == "<html><title>t</title></html>"


def test_requests_engine_is_always_available():
    assert RequestsEngine(ScraperType()).is_available() is True


def test_requests_engine_stores_session_attribute():
    fake_session = FakeSession()
    engine = RequestsEngine(ScraperType(), session=fake_session)
    assert engine.session is fake_session
