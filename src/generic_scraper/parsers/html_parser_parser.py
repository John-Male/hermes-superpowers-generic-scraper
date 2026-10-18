from __future__ import annotations

from html.parser import HTMLParser

from generic_scraper.parsers.base import ParsedDocument


class _TitleExtractingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.title: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = (self.title or "") + data


class HtmlParserParser:
    def parse(self, html: str) -> ParsedDocument:
        extractor = _TitleExtractingHTMLParser()
        extractor.feed(html)
        title = extractor.title.strip() if extractor.title else None
        return ParsedDocument(raw_html=html, title=title)
