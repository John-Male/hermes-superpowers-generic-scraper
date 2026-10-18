from __future__ import annotations

import lxml.html

from generic_scraper.parsers.base import ParsedDocument


class LxmlParser:
    def parse(self, html: str) -> ParsedDocument:
        tree = lxml.html.fromstring(html)
        title_elements = tree.xpath("//title")
        title = title_elements[0].text_content().strip() if title_elements else None
        return ParsedDocument(raw_html=html, title=title)
