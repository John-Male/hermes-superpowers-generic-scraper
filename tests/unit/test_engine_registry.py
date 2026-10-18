import pytest

from generic_scraper.engines import get_engine_class, register_engine
from generic_scraper.errors import UnsupportedScraperEngineError


def test_get_engine_class_raises_for_unknown_name():
    with pytest.raises(UnsupportedScraperEngineError):
        get_engine_class("unknown")


def test_registry_lookup_returns_registered_class():
    class DummyEngine:
        def is_available(self):
            return True

        def start(self):
            pass

        def fetch(self, url):
            return "<html></html>"

    register_engine("dummy", DummyEngine)
    assert get_engine_class("dummy") is DummyEngine
