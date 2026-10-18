from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import yaml


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

    def __post_init__(self) -> None:
        if self.retry_attempts < 1:
            raise ValueError(
                f"retry_attempts must be >= 1, got {self.retry_attempts!r}"
            )

    @staticmethod
    def empty() -> "ScraperType":
        return ScraperType()

    @staticmethod
    def from_file(path: str | Path) -> "ScraperType":
        """Load a `ScraperType` from a YAML config file.

        Top-level YAML keys matching `ScraperType` field names are used to
        construct the instance; omitted fields fall back to their dataclass
        defaults. YAML natively types `true`/`false`/digit scalars, so no
        extra string coercion is required here.
        """
        raw = yaml.safe_load(Path(path).read_text()) or {}
        if not isinstance(raw, dict):
            raise ValueError("Config file must contain a YAML mapping")
        valid_keys = {f.name for f in fields(ScraperType)}
        unknown_keys = set(raw.keys()) - valid_keys
        if unknown_keys:
            raise ValueError(
                f"Unrecognized ScraperType config key(s): "
                f"{', '.join(sorted(unknown_keys))}"
            )
        kwargs = {k: v for k, v in raw.items() if k in valid_keys}
        return ScraperType(**kwargs)
