"""Shared behave step definitions for generic-scraper feature tests.

These steps are intentionally generic so they can be reused across all
feature files in this suite: they manipulate a `context.config_kwargs`
accumulator dict, construct `ScraperType`/`Scraper` instances from it,
and assert on the resulting `Scraper` state.
"""

from __future__ import annotations

from behave import given, when, then

from generic_scraper.config import ScraperType
from generic_scraper.scraper import Scraper


def coerce(value: str) -> str | bool | int:
    """Coerce a raw step-table string into bool/int where it looks like one.

    `"true"`/`"false"` (any case) become `bool`; digit-only strings become
    `int`; everything else is left as `str`.
    """
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


@given('I have a ScraperType configuration with "{key}" set to "{value}"')
@given('"{key}" set to "{value}"')
def step_set_config_field(context, key, value):
    context.config_kwargs[key] = coerce(value)


@given("I have an empty ScraperType configuration")
def step_empty_config(context):
    context.config_kwargs = {}


@given("default scraper configuration exists")
def step_default_config_exists(context):
    # A sensible baseline that lets any engine (including browser-based
    # ones) initialize without further configuration; distinct from "an
    # empty ScraperType configuration", which deliberately has no browser
    # configured.
    context.config_kwargs = {"browser_type": "chrome"}


@when("I initialize the Scraper")
@when("I initialize the Scraper on a Swarm Forge worker")
@when("I initialize the Scraper on a worker node")
def step_initialize_scraper(context):
    context.scraper_config = ScraperType(**context.config_kwargs)
    context.init_error = None
    try:
        context.scraper = Scraper(context.scraper_config)
    except Exception as exc:  # noqa: BLE001 - captured for error-path scenarios
        context.scraper = None
        context.init_error = exc


@then('the Scraper should use the "{engine}" engine')
def step_scraper_uses_engine(context, engine):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.engine_name == engine, (
        f"Expected engine {engine!r}, got {context.scraper.engine_name!r}"
    )


@then("the Scraper should be ready to fetch pages")
def step_scraper_ready(context):
    assert context.scraper is not None, "Scraper was not initialized"
    assert hasattr(context.scraper, "fetch"), "Scraper has no fetch() method"
