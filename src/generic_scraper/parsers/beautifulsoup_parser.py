from __future__ import annotations

from bs4 import BeautifulSoup

from generic_scraper.parsers.base import ParsedDocument


class BeautifulSoupParser:
    def parse(self, html: str) -> ParsedDocument:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.title
        title = title_tag.string.strip() if title_tag and title_tag.string else None
        return ParsedDocument(raw_html=html, title=title)
