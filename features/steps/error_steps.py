"""Step definitions for `features/08_error_handling_and_retries.feature`.

Covers retry-on-transient-error behavior (via `Scraper.fetch` ->
`retry_with_backoff`), engine-start fallback behavior, and
initialization failure for unsupported engines.

The "fails to start on the worker" and "transient network error" steps
monkeypatch class-level methods (`start`/`fetch`) on the active engine
class via `unittest.mock.patch.object(...).start()`. Each patch is
registered with `context.add_cleanup(patcher.stop)` -- without this the
patched class-level method would leak into later scenarios/features in
the same behave run, exactly the pitfall `defaults_steps.py` and
`e2e_steps.py` document.

The retry-count assertion in `step_scraper_should_retry` does NOT just
check that a `ConnectionError` was eventually raised (that would pass
even if retry logic only tried once); it asserts the actual recorded
call count equals `attempts` exactly, using a counter the monkeypatched
`fetch` increments on every call.
"""

from __future__ import annotations

from unittest.mock import patch

from behave import given, when, then

from generic_scraper.config import ScraperType
from generic_scraper.engines import get_engine_class
from generic_scraper.errors import EngineUnavailableError
from generic_scraper.scraper import Scraper


@given("retry policy set to {attempts:d} attempts with exponential backoff")
def step_retry_policy(context, attempts):
    context.config_kwargs["retry_attempts"] = attempts


@when("a transient network error occurs during fetch")
def step_transient_network_error(context):
    context.scraper_config = ScraperType(**context.config_kwargs)
    context.scraper = Scraper(context.scraper_config)

    context.fetch_call_count = {"count": 0}
    call_count = context.fetch_call_count

    def always_fail(self, url):
        call_count["count"] += 1
        raise ConnectionError("simulated transient network error")

    engine_class = get_engine_class(context.scraper.engine_name)
    patcher = patch.object(engine_class, "fetch", always_fail)
    patcher.start()
    context.add_cleanup(patcher.stop)

    try:
        context.scraper.fetch("https://example.com")
        context.fetch_error = None
    except ConnectionError as exc:
        context.fetch_error = exc


@then("the Scraper should retry up to {attempts:d} times before failing")
def step_scraper_should_retry(context, attempts):
    assert context.fetch_call_count["count"] == attempts, (
        f"Expected exactly {attempts} fetch call(s), got "
        f"{context.fetch_call_count['count']}"
    )
    assert isinstance(context.fetch_error, ConnectionError), (
        f"Expected a ConnectionError to be ultimately raised, got "
        f"{context.fetch_error!r}"
    )


@given('"{engine}" fails to start on the worker')
def step_engine_fails_to_start(context, engine):
    engine_class = get_engine_class(engine)

    def always_raise_start(self):
        raise EngineUnavailableError(f"{engine!r} failed to start on the worker")

    patcher = patch.object(engine_class, "start", always_raise_start)
    patcher.start()
    context.add_cleanup(patcher.stop)


@then('the Scraper should attempt to use "{engine}" as the secondary engine')
def step_scraper_uses_secondary_engine(context, engine):
    assert context.scraper is not None, "Scraper was not initialized"
    assert context.scraper.engine_name == engine, (
        f"Expected secondary engine {engine!r}, got {context.scraper.engine_name!r}"
    )


@then("the initialization should succeed")
def step_initialization_should_succeed(context):
    assert context.init_error is None, (
        f"Expected initialization to succeed, but it raised: {context.init_error!r}"
    )
    assert context.scraper is not None, "Scraper was not initialized"


@then('the Scraper initialization should fail with "{error}"')
def step_initialization_should_fail(context, error):
    assert context.init_error is not None, (
        "Expected Scraper initialization to raise an error, but it succeeded"
    )
    assert type(context.init_error).__name__ == error, (
        f"Expected error type {error!r}, got {type(context.init_error).__name__!r}"
    )
