"""Tests for loading ScraperType configuration from a YAML file."""

from __future__ import annotations

from generic_scraper.config import ScraperType


def test_from_file_loads_yaml_config(tmp_path):
    p = tmp_path / "scraper.yaml"
    p.write_text("scraper_engine: playwright\nbrowser_type: firefox\n")
    cfg = ScraperType.from_file(p)
    assert cfg.scraper_engine == "playwright"
    assert cfg.browser_type == "firefox"


def test_from_file_applies_defaults_for_omitted_fields(tmp_path):
    p = tmp_path / "scraper.yaml"
    p.write_text("processing_type: lxml\n")
    cfg = ScraperType.from_file(p)
    assert cfg.scraper_engine == "requests"
    assert cfg.processing_type == "lxml"
