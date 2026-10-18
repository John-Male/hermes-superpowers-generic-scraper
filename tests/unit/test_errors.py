from generic_scraper.errors import (
    EngineStartError,
    EngineUnavailableError,
    ScraperError,
    UnsupportedScraperEngineError,
)


def test_unsupported_scraper_engine_error_is_scraper_error():
    assert issubclass(UnsupportedScraperEngineError, ScraperError)


def test_unsupported_scraper_engine_error_message_contains_engine_name():
    err = UnsupportedScraperEngineError("unknown")
    assert "unknown" in str(err)


def test_engine_unavailable_error_is_scraper_error():
    assert issubclass(EngineUnavailableError, ScraperError)


def test_engine_start_error_is_scraper_error():
    assert issubclass(EngineStartError, ScraperError)
