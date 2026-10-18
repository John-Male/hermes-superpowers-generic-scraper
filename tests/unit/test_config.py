from generic_scraper.config import ScraperType


def test_default_scraper_type_uses_requests_and_no_browser():
    cfg = ScraperType()
    assert cfg.scraper_engine == "requests"
    assert cfg.browser_type is None


def test_scraper_type_accepts_explicit_engine_and_browser():
    cfg = ScraperType(scraper_engine="playwright", browser_type="firefox")
    assert cfg.scraper_engine == "playwright"
    assert cfg.browser_type == "firefox"


def test_empty_factory_matches_defaults():
    assert ScraperType.empty() == ScraperType()
