from __future__ import annotations

import pytest

from generic_scraper.parsers import get_parser

SAMPLE_HTML = "<html><head><title>Example Title</title></head><body>hi</body></html>"


@pytest.mark.parametrize("processor", ["beautifulsoup", "lxml", "html.parser", "regex"])
def test_get_parser_extracts_title(processor):
    parser = get_parser(processor)
    doc = parser.parse(SAMPLE_HTML)
    assert doc.title == "Example Title"
    assert doc.raw_html == SAMPLE_HTML


def test_get_parser_rejects_unknown_processor():
    with pytest.raises(ValueError):
        get_parser("not-a-real-parser")
