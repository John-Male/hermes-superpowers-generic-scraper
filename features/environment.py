"""Behave environment hooks for generic-scraper feature tests.

`before_scenario` resets the per-scenario world: a `config_kwargs` dict
that steps accumulate `ScraperType` field values into, and a `scraper`
slot that is populated once the Scraper is initialized.

`before_all`/`after_all` patch the browser engines' default (production)
launcher/availability hooks so that a worker node is treated as able to
launch Chrome/Firefox for Playwright/Selenium by default -- real browser
automation is not implemented yet (Task 7: "mocked" engines), so without
this the happy-path "Scraper should use playwright/selenium" scenarios
could never succeed. Scenarios that need to simulate an *unavailable*
engine override this on top (their own step patches back to failure for
just that scenario).
"""

from generic_scraper.engines import playwright_engine, selenium_engine

_PATCHED_MODULES = (playwright_engine, selenium_engine)
_originals: dict[str, tuple] = {}


def _always_available():
    return True


def before_all(context):
    def _recording_launcher(browser_type):
        # Record each call's browser_type onto the context so steps can
        # assert the mocked engine actually received the expected value,
        # instead of only re-checking the input that built the config.
        context.browser_launch_calls.append(browser_type)
        return None

    for module in _PATCHED_MODULES:
        _originals[module.__name__] = (
            module._default_browser_launcher,
            module._default_availability_check,
        )
        module._default_browser_launcher = _recording_launcher
        module._default_availability_check = _always_available


def after_all(context):
    for module in _PATCHED_MODULES:
        launcher, availability = _originals[module.__name__]
        module._default_browser_launcher = launcher
        module._default_availability_check = availability


def before_scenario(context, scenario):
    context.config_kwargs = {}
    context.scraper_config = None
    context.scraper = None
    context.error = None
    context.browser_launch_calls = []


def after_scenario(context, scenario):
    pass
