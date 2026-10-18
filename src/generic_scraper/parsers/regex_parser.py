from __future__ import annotations

import re

from generic_scraper.parsers.base import ParsedDocument

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class RegexParser:
    def parse(self, html: str) -> ParsedDocument:
        match = _TITLE_RE.search(html)
        title = match.group(1).strip() if match else None
        return ParsedDocument(raw_html=html, title=title)
