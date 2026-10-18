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


def _noop_launcher(browser_type):
    return None


def _always_available():
    return True


def before_all(context):
    for module in _PATCHED_MODULES:
        _originals[module.__name__] = (
            module._default_browser_launcher,
            module._default_availability_check,
        )
        module._default_browser_launcher = _noop_launcher
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


def after_scenario(context, scenario):
    pass
