"""Step definitions for `features/06_end_to_end_fetch_parse.feature`.

These steps exercise the real `Scraper.fetch()` pipeline (retry +
engine.fetch + parser) end-to-end, without ever making a real network
call. The active engine class (whichever one the scenario configured via
`scraper_engine`) has its `fetch` method monkeypatched via
`unittest.mock.patch.object(...)` to return canned HTML containing a
`<title>`. The patch is started directly on the class (not via a fixture
decorator) so it is registered with `context.add_cleanup`, guaranteeing
it is undone after the scenario -- without this, the patched class-level
`fetch` would leak into later scenarios/features in the same behave run,
exactly the pitfall `defaults_steps.py` documents for `is_available`.
"""

from __future__ import annotations

from unittest.mock import patch

from behave import given, when, then

from generic_scraper.engines import get_engine_class

_CANNED_HTML = (
    "<html><head><title>Canned Test Page</title></head>"
    "<body><p>Canned body content.</p></body></html>"
)


@given('a test URL "{url}"')
def step_test_url(context, url):
    context.url = url


@when("I fetch the test URL")
def step_fetch_test_url(context):
    assert context.scraper is not None, "Scraper was not initialized"

    engine_class = get_engine_class(context.scraper.engine_name)
    patcher = patch.object(engine_class, "fetch", lambda self, url: _CANNED_HTML)
    patcher.start()
    context.add_cleanup(patcher.stop)

    context.parsed_doc = context.scraper.fetch(context.url)


@then('the Scraper should return a parsed document using "{processor}"')
def step_parsed_document_using_processor(context, processor):
    assert context.parsed_doc is not None, "No parsed document was produced"
    assert context.scraper.config.processing_type == processor, (
        f"Expected processing_type {processor!r}, "
        f"got {context.scraper.config.processing_type!r}"
    )


@then("the parsed document should contain the page title")
def step_parsed_document_has_title(context):
    assert context.parsed_doc is not None, "No parsed document was produced"
    assert context.parsed_doc.title, (
        f"Expected a truthy title, got {context.parsed_doc.title!r}"
    )
