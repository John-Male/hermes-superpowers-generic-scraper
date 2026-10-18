from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScraperType:
    scraper_engine: str = "requests"
    browser_type: str | None = None
    secondary: str | None = None
    use_proxy: bool = False
    proxy_url: str | None = None
    proxy_port: int | None = None
    proxy_pass_key: str | None = None
    proxy_pass_val: str | None = None
    processing_type: str = "beautifulsoup"
    retry_attempts: int = 3

    @staticmethod
    def empty() -> "ScraperType":
        return ScraperType()
