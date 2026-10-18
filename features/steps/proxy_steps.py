"""Step definitions for feature 04 (proxy and header pass-key configuration).

These steps assert against the real `requests.Session` held by the
`RequestsEngine` instance that `Scraper.__init__` constructs and starts --
no HTTP call is made; `start()` only configures `session.proxies` and
`session.headers` from the `ScraperType` config.
"""

from __future__ import annotations

from behave import then


@then('the Scraper should configure the HTTP client to use the proxy "{proxy_url}:{proxy_port}"')
def step_scraper_configures_proxy(context, proxy_url, proxy_port):
    assert context.scraper is not None, "Scraper was not initialized"
    expected = f"{proxy_url}:{proxy_port}"
    proxies = context.scraper.engine.session.proxies
    assert proxies.get("http") == expected, (
        f"Expected proxies['http'] == {expected!r}, got {proxies.get('http')!r}"
    )


@then('the Scraper should include header "{header}" on proxied requests')
def step_scraper_includes_header(context, header):
    assert context.scraper is not None, "Scraper was not initialized"
    pass_key, pass_val = header.split(": ", 1)
    headers = context.scraper.engine.session.headers
    assert headers.get(pass_key) == pass_val, (
        f"Expected headers[{pass_key!r}] == {pass_val!r}, got {headers.get(pass_key)!r}"
    )
