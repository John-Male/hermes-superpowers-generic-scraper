"""Tests for the generic_scraper CLI entry point."""

from __future__ import annotations

from generic_scraper.cli import main
from generic_scraper.engines.requests_engine import RequestsEngine


def test_main_fetches_and_prints_title(monkeypatch, capsys):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>CLI Title</title></html>")
    exit_code = main(["fetch", "https://example.com"])
    assert exit_code == 0
    assert "CLI Title" in capsys.readouterr().out


def test_main_returns_1_on_unsupported_engine(capsys):
    exit_code = main(["fetch", "https://example.com", "--engine", "not-real"])
    assert exit_code == 1


def test_main_applies_config_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>From File</title></html>")
    p = tmp_path / "cfg.yaml"
    p.write_text("processing_type: lxml\n")
    exit_code = main(["fetch", "https://example.com", "--config", str(p)])
    assert exit_code == 0
