import subprocess
import sys

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


def test_playwright_and_selenium_engines_registered_on_clean_import():
    """A fresh interpreter importing generic_scraper.engines must have
    'playwright' and 'selenium' registered, without any other test file
    having already imported those wrapper modules first.

    This genuinely exercises a clean import by running in a subprocess.
    """
    code = (
        "from generic_scraper.engines import get_engine_class; "
        "get_engine_class('playwright'); "
        "get_engine_class('selenium')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
