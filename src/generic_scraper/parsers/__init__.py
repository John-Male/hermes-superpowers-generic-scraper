from __future__ import annotations

from generic_scraper.parsers.base import ParsedDocument, Parser
from generic_scraper.parsers.beautifulsoup_parser import BeautifulSoupParser
from generic_scraper.parsers.html_parser_parser import HtmlParserParser
from generic_scraper.parsers.lxml_parser import LxmlParser
from generic_scraper.parsers.regex_parser import RegexParser

_PARSERS: dict[str, type[Parser]] = {
    "beautifulsoup": BeautifulSoupParser,
    "lxml": LxmlParser,
    "html.parser": HtmlParserParser,
    "regex": RegexParser,
}


def get_parser(processing_type: str) -> Parser:
    try:
        parser_cls = _PARSERS[processing_type]
    except KeyError as exc:
        raise ValueError(
            f"Unknown processing type: {processing_type!r}. "
            f"Valid options are: {sorted(_PARSERS)}"
        ) from exc
    return parser_cls()


__all__ = ["ParsedDocument", "Parser", "get_parser"]
