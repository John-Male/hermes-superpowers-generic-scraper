"""Behave step definitions for feature 05 (processing types)."""

from __future__ import annotations

from behave import then

from generic_scraper.parsers import get_parser
from generic_scraper.parsers.beautifulsoup_parser import BeautifulSoupParser
from generic_scraper.parsers.html_parser_parser import HtmlParserParser
from generic_scraper.parsers.lxml_parser import LxmlParser
from generic_scraper.parsers.regex_parser import RegexParser

_EXPECTED_PARSER_CLASSES = {
    "beautifulsoup": BeautifulSoupParser,
    "lxml": LxmlParser,
    "html.parser": HtmlParserParser,
    "regex": RegexParser,
}


@then('the Scraper should use "{processor}" to parse HTML responses')
def step_scraper_uses_processor(context, processor):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.config.processing_type == processor, (
        f"Expected processing_type {processor!r}, "
        f"got {context.scraper.config.processing_type!r}"
    )

    expected_cls = _EXPECTED_PARSER_CLASSES[processor]
    parser = get_parser(processor)
    assert isinstance(parser, expected_cls), (
        f"Expected get_parser({processor!r}) to return an instance of "
        f"{expected_cls.__name__}, got {type(parser).__name__}"
    )
