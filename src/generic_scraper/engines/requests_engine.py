from __future__ import annotations

import requests

from generic_scraper.config import ScraperType
from generic_scraper.engines import register_engine


class RequestsEngine:
    """Engine backed by `requests.Session`; the universal HTTP fallback."""

    browser_type: str | None = None

    def __init__(self, config: ScraperType, session: "requests.Session | None" = None):
        self.config = config
        self.session = session if session is not None else requests.Session()

    def is_available(self) -> bool:
        """requests is always available as the universal fallback."""
        return True

    def start(self) -> None:
        """Configure the session's proxies and auth header from `self.config`."""
        config = self.config
        if config.use_proxy and config.proxy_url and config.proxy_port:
            proxy_value = f"{config.proxy_url}:{config.proxy_port}"
            self.session.proxies = {"http": proxy_value, "https": proxy_value}
        if config.proxy_pass_key and config.proxy_pass_val:
            self.session.headers[config.proxy_pass_key] = config.proxy_pass_val

    def fetch(self, url: str) -> str:
        """Fetch `url` and return the raw HTML."""
        response = self.session.get(url)
        return response.text


register_engine("requests", RequestsEngine)
