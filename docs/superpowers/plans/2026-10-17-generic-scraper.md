# Generic Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Python `Scraper`/`ScraperType` package that makes all 8 Gherkin feature files pass as real `behave` tests, including a simulated (in-process) distributed job layer, plus a CLI, file-based config loading, and logging.

**Architecture:** A `src/generic_scraper` package with pluggable `Engine` and `Parser` strategy classes behind registries/factories, a `Scraper` orchestrator that wires config → engine selection/fallback → retry → fetch → parse, and a separate `distributed` subpackage simulating node placement, job sharding, and artifact storage in-process. `behave` step definitions under `features/steps/` exercise the package against the 8 existing `.feature` files with engines/browsers mocked at the boundary (no real browser binaries, no real network).

**Tech Stack:** Python 3.11+, `behave` (BDD runner), `pytest` (unit tests), `requests`, `playwright` and `selenium` as optional/mocked dependencies, `beautifulsoup4`, `lxml`, stdlib `html.parser` and `re`, `PyYAML` for config files, stdlib `logging`, `argparse` for the CLI, `pyproject.toml` with a `src/` layout.

**Spec:** `docs/superpowers/specs/2026-10-17-generic-scraper-design.md`

## Global Constraints

- Language/stack: Python, `src/` layout, `pyproject.toml`.
- The 8 files in `features/` are the spec of record and must not be rewritten to fit the implementation.
- No real network calls or real browser launches anywhere in the test suite; engine/browser/HTTP interactions are mocked/faked at the boundary.
- Default scraper engine is `"requests"`; default browser is unconfigured (`None`).
- `UnsupportedScraperEngineError` is the exact exception name/message category required by feature 08-3.
- Feature 07's distributed behavior (shards, worker nodes, artifact store, node affinity/resource limits) is simulated in-process only — no real cluster, no real network storage.
- Every task's tests must actually fail before the implementation step and pass after (TDD), and every task ends in a commit.

## Review Focus

- Empty/missing `ScraperType` fields beyond the ones a scenario sets explicitly (e.g. `use_proxy=False` with no proxy URL) should not crash `Scraper` init — a reasonable person expects "no proxy configured" to just mean no proxy, not an error.
- An engine that is both unavailable and has no `secondary` configured, and is not `requests` itself, must still degrade to `requests` (feature 03-2) rather than raising — only a truly unknown engine name raises `UnsupportedScraperEngineError` (feature 08-3).
- Retry must not retry forever or retry non-transient errors (e.g. an `UnsupportedScraperEngineError`) — a reasonable person expects retry to apply only to the fetch step's transient network failures, not configuration errors.
- `regex` as a `processing_type` must still produce a parsed document whose title is extractable, even though it isn't a real HTML parser library — this is easy to half-implement as a no-op.
- The distributed node registry must genuinely reject placements that don't satisfy requested constraints (GPU/memory/browser), not just always return the first node — otherwise feature 07-3 passes without the logic it's supposed to test.

---

## Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/generic_scraper/__init__.py`
- Create: `behave.ini` (or `[behave]` section in `tox.ini`/`setup.cfg` — builder's call)
- Create: `features/environment.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: an installable package `generic_scraper` (editable install via `pip install -e .`), a working `behave` invocation (`behave` from repo root discovers `features/`), a working `pytest` invocation (`pytest tests/`).

- [ ] **Step 1: Write `pyproject.toml`** with project metadata, `src/` layout (`[tool.setuptools.packages.find] where = ["src"]`), dependencies (`requests`, `beautifulsoup4`, `lxml`, `PyYAML`), optional-dependencies group `browsers` for `playwright`/`selenium`, and dev dependencies (`behave`, `pytest`) as an extras group `dev`.
- [ ] **Step 2: Create `src/generic_scraper/__init__.py`** (empty, just makes the package importable) and `tests/__init__.py`.
- [ ] **Step 3: Create `features/environment.py`** with an empty `before_all(context)`/`after_all(context)` pair (hooks get filled in by later tasks; this just proves `behave` can load the environment file without error).
- [ ] **Step 4: Install the package editable and run the empty suites**

Run: `pip install -e ".[dev,browsers]"` then `behave` and `pytest tests/`
Expected: `behave` reports all scenarios as "undefined steps" (no step definitions yet, no errors loading); `pytest` reports "no tests ran" with exit code 0 or 5.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/generic_scraper/__init__.py features/environment.py tests/__init__.py .gitignore
git commit -m "chore: project scaffolding (src layout, behave, pytest)"
```

---

## Task 2: Error hierarchy

**Files:**
- Create: `src/generic_scraper/errors.py`
- Test: `tests/unit/test_errors.py`

**Interfaces:**
- Produces: `class ScraperError(Exception)`, `class UnsupportedScraperEngineError(ScraperError)`, `class EngineUnavailableError(ScraperError)` (raised internally when an engine fails its capability check or fails to start), `class EngineStartError(ScraperError)` (alias or subclass used for "fails to start on the worker" scenarios — builder's call whether this is the same class as `EngineUnavailableError` or distinct).

- [ ] **Step 1: Write failing tests**

```python
def test_unsupported_scraper_engine_error_is_scraper_error():
    assert issubclass(UnsupportedScraperEngineError, ScraperError)

def test_unsupported_scraper_engine_error_message_contains_engine_name():
    err = UnsupportedScraperEngineError("unknown")
    assert "unknown" in str(err)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError` / `ImportError`.

- [ ] **Step 3: Implement the error classes in `src/generic_scraper/errors.py`**

`UnsupportedScraperEngineError.__init__(self, engine_name: str)` sets a message like `f"Unsupported scraper engine: {engine_name!r}"`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/errors.py tests/unit/test_errors.py
git commit -m "feat: error hierarchy"
```

---

## Task 3: ScraperType configuration

**Files:**
- Create: `src/generic_scraper/config.py`
- Test: `tests/unit/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `@dataclass class ScraperType` with fields: `scraper_engine: str = "requests"`, `browser_type: str | None = None`, `secondary: str | None = None`, `use_proxy: bool = False`, `proxy_url: str | None = None`, `proxy_port: int | None = None`, `proxy_pass_key: str | None = None`, `proxy_pass_val: str | None = None`, `processing_type: str = "beautifulsoup"`, `retry_attempts: int = 3`. Also `ScraperType.empty() -> ScraperType` (all defaults, used by feature 03-1's "empty ScraperType configuration").

- [ ] **Step 1: Write failing tests**

```python
def test_default_scraper_type_uses_requests_and_no_browser():
    cfg = ScraperType()
    assert cfg.scraper_engine == "requests"
    assert cfg.browser_type is None

def test_scraper_type_accepts_explicit_engine_and_browser():
    cfg = ScraperType(scraper_engine="playwright", browser_type="firefox")
    assert cfg.scraper_engine == "playwright"
    assert cfg.browser_type == "firefox"

def test_empty_factory_matches_defaults():
    assert ScraperType.empty() == ScraperType()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `ScraperType`** as described above (plain `@dataclass`, `empty` is a `@staticmethod`/`@classmethod` returning `ScraperType()`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/config.py tests/unit/test_config.py
git commit -m "feat: ScraperType configuration dataclass"
```

---

## Task 4: Parser abstraction (all 4 processing types)

**Files:**
- Create: `src/generic_scraper/parsers/__init__.py`
- Create: `src/generic_scraper/parsers/base.py`
- Create: `src/generic_scraper/parsers/beautifulsoup_parser.py`
- Create: `src/generic_scraper/parsers/lxml_parser.py`
- Create: `src/generic_scraper/parsers/html_parser_parser.py`
- Create: `src/generic_scraper/parsers/regex_parser.py`
- Test: `tests/unit/test_parsers.py`

**Interfaces:**
- Consumes: raw HTML `str`.
- Produces: `class ParsedDocument` with `.title: str | None` and `.raw_html: str`; `def get_parser(processing_type: str) -> Parser` factory in `parsers/__init__.py` raising `ValueError` for unknown processor names; each parser module exposes a class implementing `def parse(self, html: str) -> ParsedDocument`.

- [ ] **Step 1: Write failing tests** (parametrized over all 4 processors) using a fixed HTML sample with a known `<title>`:

```python
SAMPLE_HTML = "<html><head><title>Example Title</title></head><body>hi</body></html>"

@pytest.mark.parametrize("processor", ["beautifulsoup", "lxml", "html.parser", "regex"])
def test_get_parser_extracts_title(processor):
    parser = get_parser(processor)
    doc = parser.parse(SAMPLE_HTML)
    assert doc.title == "Example Title"

def test_get_parser_rejects_unknown_processor():
    with pytest.raises(ValueError):
        get_parser("not-a-real-parser")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_parsers.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement each parser and the registry.** `beautifulsoup_parser` uses `bs4.BeautifulSoup(html, "html.parser")`, `lxml_parser` uses `lxml.html.fromstring`, `html_parser_parser` subclasses stdlib `html.parser.HTMLParser` to capture the `<title>` text, `regex_parser` uses `re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)`. `get_parser` is a `dict`-based registry keyed by the four exact strings from the feature file.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_parsers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/parsers tests/unit/test_parsers.py
git commit -m "feat: parser abstraction for 4 processing types"
```

---

## Task 5: Engine abstraction, registry, and capability-check seam

**Files:**
- Create: `src/generic_scraper/engines/__init__.py`
- Create: `src/generic_scraper/engines/base.py`
- Test: `tests/unit/test_engine_registry.py`

**Interfaces:**
- Consumes: `errors.UnsupportedScraperEngineError`.
- Produces: `class Engine(Protocol)` (or ABC) with `def is_available(self) -> bool`, `def start(self) -> None` (raises `EngineUnavailableError`/`EngineStartError` on failure), `def fetch(self, url: str) -> str` (returns raw HTML), and an optional `browser_type: str | None` attribute. `def get_engine_class(name: str) -> type[Engine]` in `engines/__init__.py`, raising `UnsupportedScraperEngineError(name)` for unknown names. The registry maps `"requests"`, `"playwright"`, `"selenium"` to their (not-yet-written) classes — this task defines the interface and registry wiring with a `DummyEngine` test double; Tasks 6–7 add the real classes.

- [ ] **Step 1: Write failing tests** using a local `DummyEngine` registered into a throwaway registry instance (not the module-level one) to test registry mechanics in isolation:

```python
def test_get_engine_class_raises_for_unknown_name():
    with pytest.raises(UnsupportedScraperEngineError):
        get_engine_class("unknown")

def test_registry_lookup_returns_registered_class():
    class DummyEngine:
        def is_available(self): return True
        def start(self): pass
        def fetch(self, url): return "<html></html>"
    register_engine("dummy", DummyEngine)
    assert get_engine_class("dummy") is DummyEngine
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_engine_registry.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `Engine` protocol in `base.py` and a module-level dict registry with `register_engine(name, cls)` / `get_engine_class(name)` in `engines/__init__.py`.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_engine_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/engines/base.py src/generic_scraper/engines/__init__.py tests/unit/test_engine_registry.py
git commit -m "feat: engine interface and registry"
```

---

## Task 6: RequestsEngine with proxy and header support

**Files:**
- Create: `src/generic_scraper/engines/requests_engine.py`
- Test: `tests/unit/test_requests_engine.py`

**Interfaces:**
- Consumes: `engines.base.Engine`, `engines.register_engine`, `config.ScraperType`.
- Produces: `class RequestsEngine` constructed as `RequestsEngine(config: ScraperType)`, registered under `"requests"`. `fetch(url)` uses a `requests.Session` (injectable via an optional `session=` constructor param for tests) configured with `session.proxies = {"http": f"{proxy_url}:{proxy_port}", "https": f"{proxy_url}:{proxy_port}"}` when `config.use_proxy` is true, and `session.headers[config.proxy_pass_key] = config.proxy_pass_val` when both are set. `is_available()` returns `True` (requests is always available as the universal fallback).

- [ ] **Step 1: Write failing tests** using a fake `session` object (e.g. `unittest.mock.Mock()` or a tiny fake class recording calls) instead of real HTTP:

```python
def test_requests_engine_configures_proxy_on_session():
    cfg = ScraperType(use_proxy=True, proxy_url="http://proxy.example", proxy_port=8080)
    fake_session = FakeSession()
    engine = RequestsEngine(cfg, session=fake_session)
    engine.start()
    assert fake_session.proxies == {
        "http": "http://proxy.example:8080",
        "https": "http://proxy.example:8080",
    }

def test_requests_engine_sets_pass_key_header():
    cfg = ScraperType(proxy_pass_key="X-Proxy-Auth", proxy_pass_val="dummy-token-abc")
    fake_session = FakeSession()
    engine = RequestsEngine(cfg, session=fake_session)
    engine.start()
    assert fake_session.headers["X-Proxy-Auth"] == "dummy-token-abc"

def test_requests_engine_fetch_returns_response_text():
    fake_session = FakeSession(get_text="<html><title>t</title></html>")
    engine = RequestsEngine(ScraperType(), session=fake_session)
    engine.start()
    assert engine.fetch("https://example.com") == "<html><title>t</title></html>"

def test_requests_engine_is_always_available():
    assert RequestsEngine(ScraperType()).is_available() is True
```

(`FakeSession` is a small test helper in the same test file recording `.proxies`, `.headers` dicts and returning a canned `.get(url).text`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_requests_engine.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `RequestsEngine`** and call `register_engine("requests", RequestsEngine)` at module import time (imported by `engines/__init__.py` so the registry is always populated).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_requests_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/engines/requests_engine.py tests/unit/test_requests_engine.py
git commit -m "feat: RequestsEngine with proxy and header support"
```

---

## Task 7: PlaywrightEngine and SeleniumEngine (mocked)

**Files:**
- Create: `src/generic_scraper/engines/playwright_engine.py`
- Create: `src/generic_scraper/engines/selenium_engine.py`
- Test: `tests/unit/test_browser_engines.py`

**Interfaces:**
- Consumes: `engines.base.Engine`, `config.ScraperType`, `errors.EngineUnavailableError`.
- Produces: `class PlaywrightEngine` and `class SeleniumEngine`, each constructed as `Engine(config, browser_launcher=...)` where `browser_launcher` is an injectable callable defaulting to a thin real wrapper (not exercised by tests) that the test suite replaces with a fake recording which `browser_type` was requested. `is_available()` performs a real but overridable capability check: `try: import playwright` / `try: import selenium`, wrapped so a constructor-injected `availability_check` callable overrides it for tests. `start()` calls `browser_launcher(self.config.browser_type)`; raises `EngineUnavailableError` if `browser_type` is not one of `"chrome"`/`"firefox"`.

- [ ] **Step 1: Write failing tests**, parametrized over `("playwright", PlaywrightEngine)` and `("selenium", SeleniumEngine)`, and over `browser in ("chrome", "firefox")`:

```python
@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
@pytest.mark.parametrize("browser", ["chrome", "firefox"])
def test_engine_launches_configured_browser(engine_cls, browser):
    cfg = ScraperType(browser_type=browser)
    launches = []
    engine = engine_cls(cfg, browser_launcher=launches.append, availability_check=lambda: True)
    engine.start()
    assert launches == [browser]

@pytest.mark.parametrize("engine_cls", [PlaywrightEngine, SeleniumEngine])
def test_engine_unavailable_when_check_fails(engine_cls):
    engine = engine_cls(ScraperType(browser_type="chrome"), availability_check=lambda: False)
    assert engine.is_available() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_browser_engines.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement both engine classes** sharing the described constructor shape; register them under `"playwright"` / `"selenium"` in their modules.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_browser_engines.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/engines/playwright_engine.py src/generic_scraper/engines/selenium_engine.py tests/unit/test_browser_engines.py
git commit -m "feat: PlaywrightEngine and SeleniumEngine (mocked)"
```

---

## Task 8: Retry/backoff utility

**Files:**
- Create: `src/generic_scraper/retry.py`
- Test: `tests/unit/test_retry.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `def retry_with_backoff(fn: Callable[[], T], attempts: int, retry_on: tuple[type[Exception], ...], base_delay: float = 0.01, multiplier: float = 2.0, sleep: Callable[[float], None] = time.sleep) -> T`. Calls `fn()`; on an exception in `retry_on`, sleeps `base_delay * multiplier ** attempt_index` and retries up to `attempts` total calls; re-raises the last exception if all attempts fail. `sleep` is injectable so tests run instantly.

- [ ] **Step 1: Write failing tests**

```python
def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("boom")
        return "ok"
    result = retry_with_backoff(flaky, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)
    assert result == "ok"
    assert calls["n"] == 3

def test_retry_raises_after_exhausting_attempts():
    def always_fails():
        raise ConnectionError("boom")
    with pytest.raises(ConnectionError):
        retry_with_backoff(always_fails, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)

def test_retry_does_not_catch_unlisted_exceptions():
    def raises_value_error():
        raise ValueError("not transient")
    with pytest.raises(ValueError):
        retry_with_backoff(raises_value_error, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_retry.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `retry_with_backoff`** as described.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_retry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/retry.py tests/unit/test_retry.py
git commit -m "feat: retry with exponential backoff"
```

---

## Task 9: Scraper orchestrator — init, defaults, and fallback

**Files:**
- Create: `src/generic_scraper/scraper.py`
- Test: `tests/unit/test_scraper_init.py`

**Interfaces:**
- Consumes: `config.ScraperType`, `engines.get_engine_class`, `errors.{UnsupportedScraperEngineError, EngineUnavailableError}`.
- Produces: `class Scraper` constructed as `Scraper(config: ScraperType)`. On `__init__`: looks up `config.scraper_engine` via `get_engine_class` (propagates `UnsupportedScraperEngineError` for unknown names); instantiates and checks `is_available()`/`start()`; on unavailability/`EngineUnavailableError`, falls back to `config.secondary` if set, else to `"requests"` (unless the primary already was `"requests"`, in which case the error propagates — matches feature 08-3 where `"unknown"` has no fallback path). Exposes `self.engine_name: str` (the engine actually in use after fallback) and `self.engine: Engine`.

- [ ] **Step 1: Write failing tests**

```python
def test_scraper_uses_requests_engine_by_default():
    scraper = Scraper(ScraperType.empty())
    assert scraper.engine_name == "requests"

def test_scraper_raises_for_unsupported_engine():
    with pytest.raises(UnsupportedScraperEngineError):
        Scraper(ScraperType(scraper_engine="unknown"))

def test_scraper_falls_back_to_requests_when_primary_unavailable(monkeypatch):
    # monkeypatch PlaywrightEngine.is_available to return False
    monkeypatch.setattr(PlaywrightEngine, "is_available", lambda self: False)
    scraper = Scraper(ScraperType(scraper_engine="playwright"))
    assert scraper.engine_name == "requests"

def test_scraper_falls_back_to_configured_secondary(monkeypatch):
    monkeypatch.setattr(SeleniumEngine, "start", lambda self: (_ for _ in ()).throw(EngineUnavailableError("selenium")))
    scraper = Scraper(ScraperType(scraper_engine="selenium", secondary="requests"))
    assert scraper.engine_name == "requests"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_scraper_init.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `Scraper.__init__`** with the fallback algorithm described above.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_scraper_init.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/scraper.py tests/unit/test_scraper_init.py
git commit -m "feat: Scraper init with engine fallback"
```

---

## Task 10: Scraper.fetch — retry, parse, and end-to-end wiring

**Files:**
- Modify: `src/generic_scraper/scraper.py`
- Test: `tests/unit/test_scraper_fetch.py`

**Interfaces:**
- Consumes: `retry.retry_with_backoff`, `parsers.get_parser`, `Scraper` from Task 9.
- Produces: `Scraper.fetch(self, url: str) -> ParsedDocument`. Wraps `self.engine.fetch(url)` in `retry_with_backoff(..., attempts=config.retry_attempts, retry_on=(ConnectionError, TimeoutError))`, then passes the resulting HTML to `get_parser(config.processing_type).parse(html)` and returns the `ParsedDocument`.

- [ ] **Step 1: Write failing tests**

```python
def test_fetch_returns_parsed_document_with_title(monkeypatch):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>Example</title></html>")
    scraper = Scraper(ScraperType())
    doc = scraper.fetch("https://example.com/test-page")
    assert doc.title == "Example"

def test_fetch_retries_transient_errors_then_succeeds(monkeypatch):
    calls = {"n": 0}
    def flaky_fetch(self, url):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("boom")
        return "<html><title>Recovered</title></html>"
    monkeypatch.setattr(RequestsEngine, "fetch", flaky_fetch)
    scraper = Scraper(ScraperType(retry_attempts=3))
    doc = scraper.fetch("https://example.com")
    assert doc.title == "Recovered"
    assert calls["n"] == 2

def test_fetch_gives_up_after_retry_attempts_exhausted(monkeypatch):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: (_ for _ in ()).throw(ConnectionError("boom")))
    scraper = Scraper(ScraperType(retry_attempts=3))
    with pytest.raises(ConnectionError):
        scraper.fetch("https://example.com")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_scraper_fetch.py -v`
Expected: FAIL with `AttributeError: 'Scraper' object has no attribute 'fetch'`.

- [ ] **Step 3: Implement `Scraper.fetch`** as described (use a fast `sleep=lambda s: None` or a small default base delay so real tests stay fast; the default `retry_with_backoff` sleep can remain `time.sleep` for production use since `base_delay` stays tiny, e.g. `0.01`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_scraper_fetch.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/scraper.py tests/unit/test_scraper_fetch.py
git commit -m "feat: Scraper.fetch with retry and parsing"
```

---

## Task 11: Behave support code (world object + shared steps)

**Files:**
- Modify: `features/environment.py`
- Create: `features/steps/common_steps.py`

**Interfaces:**
- Consumes: `config.ScraperType`, `scraper.Scraper`.
- Produces: a `context.config_kwargs: dict` accumulator and `context.scraper: Scraper | None` set up per-scenario in `before_scenario`; shared steps: `Given I have a ScraperType configuration with "{key}" set to "{value}"`, `And "{key}" set to "{value}"` (applies to the same accumulator — used as a continuation step across several feature files), `Given I have an empty ScraperType configuration`, `Given default scraper configuration exists`, `When I initialize the Scraper` / `When I initialize the Scraper on a Swarm Forge worker` / `When I initialize the Scraper on a worker node` (all three bind to one implementation, per the design doc's "cosmetic wording" decision), `Then the Scraper should use the "{engine}" engine`, `Then the Scraper should be ready to fetch pages`. Boolean/int-looking string values (`"true"`, `"8080"`) are coerced appropriately when assigned onto `ScraperType` fields.

- [ ] **Step 1: Write a failing behave run targeting feature 01 only**

Run: `behave features/01_initialize_scraper.feature`
Expected: FAIL/undefined — steps not yet defined (confirm this before writing steps, per TDD-for-BDD).

- [ ] **Step 2: Implement `features/environment.py` hooks and `features/steps/common_steps.py`** with the steps listed above. Use a small helper `coerce(value: str) -> str | bool | int` (`"true"`/`"false"` → `bool`, digit strings → `int`, else leave as `str`) when setting attributes on the accumulated kwargs dict before constructing `ScraperType(**kwargs)`.

- [ ] **Step 3: Run feature 01 and verify it passes**

Run: `behave features/01_initialize_scraper.feature`
Expected: 1 feature passed, 3 scenarios passed (requests/playwright/selenium).

- [ ] **Step 4: Commit**

```bash
git add features/environment.py features/steps/common_steps.py
git commit -m "feat: behave world setup and shared steps; feature 01 passing"
```

---

## Task 12: Feature 02 — browser configuration steps

**Files:**
- Create: `features/steps/browser_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`'s accumulator pattern, `Scraper`.
- Produces: `Then the Scraper should launch "{browser}" for "{engine}"` — asserts `context.scraper.config.browser_type == browser` and `context.scraper.engine_name == engine` (with engines mocked so no real browser opens; `is_available`/`start` are monkeypatched via the engine's injectable `availability_check`/`browser_launcher` seams from Task 7 — wire that injection through `Scraper`'s construction path, e.g. a `Scraper` class-level factory override the step can set in `before_scenario`/`before_feature`, or construct the engine directly and swap `context.scraper.engine` after init if that's simpler — builder's call, document whichever is chosen in a code comment).

- [ ] **Step 1: Run feature 02 to confirm it currently fails/undefined**

Run: `behave features/02_browser_configuration.feature`
Expected: undefined step `Then the Scraper should launch...`.

- [ ] **Step 2: Implement the step** and whatever minimal seam is needed in `Scraper`/engines so browser launches are observable without a real browser.

- [ ] **Step 3: Run feature 02 and verify it passes**

Run: `behave features/02_browser_configuration.feature`
Expected: 1 feature passed, 4 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/browser_steps.py
git commit -m "feat: feature 02 browser configuration steps passing"
```

---

## Task 13: Feature 03 — defaults and fallback steps

**Files:**
- Create: `features/steps/defaults_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `Scraper`.
- Produces: `Given "{engine}" is not available on the worker node` (forces that engine's `is_available`/`start` to fail for this scenario, e.g. by monkeypatching via `behave`'s `context` and Python's `unittest.mock.patch.object`, undone in `after_scenario`), `Then the Scraper should fall back to "{engine}"`, `Then the Scraper should have no browser configured`.

- [ ] **Step 1: Run feature 03 to confirm it currently fails/undefined**

Run: `behave features/03_defaults_and_fallbacks.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the steps**, reusing the unavailability monkeypatch pattern from Task 9's unit tests.

- [ ] **Step 3: Run feature 03 and verify it passes**

Run: `behave features/03_defaults_and_fallbacks.feature`
Expected: 1 feature passed, 3 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/defaults_steps.py
git commit -m "feat: feature 03 defaults and fallback steps passing"
```

---

## Task 14: Feature 04 — proxy and headers steps

**Files:**
- Create: `features/steps/proxy_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `Scraper`, `RequestsEngine`'s injectable `session`.
- Produces: `Then the Scraper should configure the HTTP client to use the proxy "{proxy_url}:{proxy_port}"` (asserts `context.scraper.engine.session.proxies["http"] == f"{proxy_url}:{proxy_port}"`), `Then the Scraper should include header "{pass_key}: {pass_val}" on proxied requests` (asserts `context.scraper.engine.session.headers[pass_key] == pass_val`; the step must split on the literal `": "` from the Gherkin string).

- [ ] **Step 1: Run feature 04 to confirm it currently fails/undefined**

Run: `behave features/04_proxy_and_headers.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the steps.** Ensure `RequestsEngine` is constructed with a real (non-mocked) `requests.Session` by default here so `.proxies`/`.headers` are real dict-likes to assert against (no actual HTTP call happens in these scenarios — only `start()` configuring the session is exercised).

- [ ] **Step 3: Run feature 04 and verify it passes**

Run: `behave features/04_proxy_and_headers.feature`
Expected: 1 feature passed, 4 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/proxy_steps.py
git commit -m "feat: feature 04 proxy and headers steps passing"
```

---

## Task 15: Feature 05 — processing types steps

**Files:**
- Create: `features/steps/processing_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `Scraper`.
- Produces: `Then the Scraper should use "{processor}" to parse HTML responses` — asserts `context.scraper.config.processing_type == processor` and that `get_parser(processor)` returns an instance of the expected parser class (import the four parser classes and map processor name → class for the assertion).

- [ ] **Step 1: Run feature 05 to confirm it currently fails/undefined**

Run: `behave features/05_processing_types.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the step.**

- [ ] **Step 3: Run feature 05 and verify it passes**

Run: `behave features/05_processing_types.feature`
Expected: 1 feature passed, 4 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/processing_steps.py
git commit -m "feat: feature 05 processing types steps passing"
```

---

## Task 16: Feature 06 — end-to-end fetch and parse steps

**Files:**
- Create: `features/steps/e2e_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `Scraper.fetch`.
- Produces: `Given a test URL "{url}"`, `When I fetch the test URL` (calls `context.scraper.fetch(context.url)`, storing the result on `context.parsed_doc`; the underlying engine's `fetch` is monkeypatched in `before_scenario` for this feature file to return a canned HTML string containing a `<title>` so no real network call happens), `Then the Scraper should return a parsed document using "{processor}"`, `Then the parsed document should contain the page title` (asserts `context.parsed_doc.title` is truthy).

- [ ] **Step 1: Run feature 06 to confirm it currently fails/undefined**

Run: `behave features/06_end_to_end_fetch_parse.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the steps**, with the canned-HTML monkeypatch applied to whichever engine class is in play for each scenario row (`requests`/`selenium`/`playwright`).

- [ ] **Step 3: Run feature 06 and verify it passes**

Run: `behave features/06_end_to_end_fetch_parse.feature`
Expected: 1 feature passed, 4 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/e2e_steps.py
git commit -m "feat: feature 06 end-to-end fetch/parse steps passing"
```

---

## Task 17: Feature 08 — error handling and retries steps

**Files:**
- Create: `features/steps/error_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `Scraper`, `retry.retry_with_backoff`.
- Produces: `Given retry policy set to {attempts:d} attempts with exponential backoff` (sets `retry_attempts` in the accumulator), `When a transient network error occurs during fetch` (monkeypatches the active engine's `fetch` to always raise `ConnectionError` and records call count), `Then the Scraper should retry up to {attempts:d} times before failing` (asserts the recorded call count equals `attempts` and that a `ConnectionError` was ultimately raised), `Given "{engine}" fails to start on the worker` (forces `start()` to raise `EngineUnavailableError`), `Then the Scraper should attempt to use "{engine}" as the secondary engine` / `Then the initialization should succeed`, `Then the Scraper initialization should fail with "{error}"` (asserts the raised exception's class name equals `error`, catching it around the `Scraper(...)` construction in the `When` step).

- [ ] **Step 1: Run feature 08 to confirm it currently fails/undefined**

Run: `behave features/08_error_handling_and_retries.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the steps.**

- [ ] **Step 3: Run feature 08 and verify it passes**

Run: `behave features/08_error_handling_and_retries.feature`
Expected: 1 feature passed, 5 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/error_steps.py
git commit -m "feat: feature 08 error handling and retries steps passing"
```

---

## Task 18: Simulated node registry (distributed layer, part 1)

**Files:**
- Create: `src/generic_scraper/distributed/__init__.py`
- Create: `src/generic_scraper/distributed/nodes.py`
- Test: `tests/unit/test_nodes.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `@dataclass class Node`: `node_id: str`, `has_gpu: bool`, `memory_gb: int`, `browsers: frozenset[str] = frozenset()`. `class NodeRegistry`: `register(self, node: Node) -> None`, `def find_matching_node(self, *, requires_gpu: bool = False, min_memory_gb: int = 0, browser: str | None = None) -> Node | None` (returns the first registered node satisfying all constraints, or `None`). `def default_registry() -> NodeRegistry` seeding at least 3 varied nodes (e.g. one with `chrome` + 1GB + no GPU, one with `chrome`+`firefox` + 4GB + no GPU, one with no browsers + 8GB + GPU) so constraint filtering has something real to filter.

- [ ] **Step 1: Write failing tests**

```python
def test_find_matching_node_respects_memory_and_browser():
    registry = NodeRegistry()
    registry.register(Node("n1", has_gpu=False, memory_gb=1, browsers=frozenset({"chrome"})))
    registry.register(Node("n2", has_gpu=False, memory_gb=4, browsers=frozenset({"chrome", "firefox"})))
    match = registry.find_matching_node(min_memory_gb=2, browser="chrome")
    assert match.node_id == "n2"

def test_find_matching_node_returns_none_when_no_node_qualifies():
    registry = NodeRegistry()
    registry.register(Node("n1", has_gpu=False, memory_gb=1))
    assert registry.find_matching_node(requires_gpu=True) is None

def test_default_registry_has_a_node_satisfying_chrome_2gb_no_gpu():
    registry = default_registry()
    match = registry.find_matching_node(requires_gpu=False, min_memory_gb=2, browser="chrome")
    assert match is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_nodes.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `Node`, `NodeRegistry`, `default_registry`.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_nodes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/distributed/__init__.py src/generic_scraper/distributed/nodes.py tests/unit/test_nodes.py
git commit -m "feat: simulated node registry with resource/affinity matching"
```

---

## Task 19: Simulated artifact store and job orchestrator (distributed layer, part 2)

**Files:**
- Create: `src/generic_scraper/distributed/artifacts.py`
- Create: `src/generic_scraper/distributed/orchestrator.py`
- Test: `tests/unit/test_distributed_job.py`

**Interfaces:**
- Consumes: `distributed.nodes.{Node, NodeRegistry, default_registry}`, `scraper.Scraper`, `config.ScraperType`.
- Produces:
  - `class ArtifactStore`: `upload(self, name: str, data: bytes | str) -> None`, `exists(self, name: str) -> bool`, `get(self, name: str) -> bytes | str`. In-memory dict-backed by default.
  - `@dataclass class ShardResult`: `worker_id: str`, `artifact_name: str`.
  - `class Orchestrator(registry: NodeRegistry, artifact_store: ArtifactStore)`: `def schedule(self, config: ScraperType, shards: int, fetch_fn: Callable[[], str] | None = None) -> list[ShardResult]` — assigns each shard a distinct simulated `worker_id` (e.g. `f"worker-{i}"`), runs `fetch_fn` (default: a canned HTML string, no real network) through a `Scraper`-driven parse, and uploads a `parsed_result.json`-named artifact per shard (namespaced per worker, e.g. `f"{worker_id}/parsed_result.json"`) to `artifact_store`. `def schedule_with_constraints(self, *, requires_gpu: bool, min_memory_gb: int, browser: str | None) -> Node` — delegates to `registry.find_matching_node`, raising a `NoSuitableNodeError` (new, in `errors.py`) if `None`.

- [ ] **Step 1: Write failing tests**

```python
def test_schedule_runs_distinct_workers_per_shard():
    orch = Orchestrator(default_registry(), ArtifactStore())
    results = orch.schedule(ScraperType(), shards=3)
    assert len({r.worker_id for r in results}) == 3

def test_schedule_uploads_artifact_per_shard():
    store = ArtifactStore()
    orch = Orchestrator(default_registry(), store)
    results = orch.schedule(ScraperType(), shards=2)
    for r in results:
        assert store.exists(f"{r.worker_id}/parsed_result.json")

def test_schedule_with_constraints_returns_satisfying_node():
    orch = Orchestrator(default_registry(), ArtifactStore())
    node = orch.schedule_with_constraints(requires_gpu=False, min_memory_gb=2, browser="chrome")
    assert node.memory_gb >= 2 and "chrome" in node.browsers and not node.has_gpu

def test_schedule_with_constraints_raises_when_unsatisfiable():
    orch = Orchestrator(default_registry(), ArtifactStore())
    with pytest.raises(NoSuitableNodeError):
        orch.schedule_with_constraints(requires_gpu=True, min_memory_gb=9999, browser="chrome")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_distributed_job.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add `NoSuitableNodeError` to `errors.py`; implement `ArtifactStore` and `Orchestrator`.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_distributed_job.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/distributed/artifacts.py src/generic_scraper/distributed/orchestrator.py src/generic_scraper/errors.py tests/unit/test_distributed_job.py
git commit -m "feat: simulated artifact store and job orchestrator"
```

---

## Task 20: Feature 07 — distributed execution and artifacts steps

**Files:**
- Create: `features/steps/distributed_steps.py`

**Interfaces:**
- Consumes: `common_steps.py`, `distributed.orchestrator.Orchestrator`, `distributed.nodes.default_registry`, `distributed.artifacts.ArtifactStore`.
- Produces: `Given the job is configured to run with {shards:d} parallel shards`, `When the orchestrator schedules the job` (calls `Orchestrator(...).schedule(...)`, storing results on `context.shard_results`), `Then the job should run on {shards:d} distinct worker nodes`, `Then each worker should produce a parsed artifact`, `Given a worker produced "{artifact}"` / `When the worker finishes the shard` / `Then the artifact "{artifact}" should be uploaded to the job artifact store`, `Given the job requests GPU {gpu_flag} and memory {memory}` (parses `"false"/"true"` and `"2GB"` style strings), `Then the job should be placed on a node that satisfies the resource constraints` (calls `schedule_with_constraints` and asserts no exception / a `Node` is returned).

- [ ] **Step 1: Run feature 07 to confirm it currently fails/undefined**

Run: `behave features/07_distributed_execution_and_artifacts.feature`
Expected: undefined steps.

- [ ] **Step 2: Implement the steps.**

- [ ] **Step 3: Run feature 07 and verify it passes**

Run: `behave features/07_distributed_execution_and_artifacts.feature`
Expected: 1 feature passed, 4 scenarios passed.

- [ ] **Step 4: Commit**

```bash
git add features/steps/distributed_steps.py
git commit -m "feat: feature 07 distributed execution steps passing"
```

---

## Task 21: Full behave suite green

**Files:** none (verification only)

- [ ] **Step 1: Run the full suite**

Run: `behave`
Expected: 8 features passed, 31 scenarios passed, 0 failed, 0 undefined.

- [ ] **Step 2: Run the full unit suite**

Run: `pytest tests/ -v`
Expected: all tests passed.

- [ ] **Step 3: Commit** (only if Step 1/2 required any fix-up changes; otherwise skip the commit — this task is a checkpoint)

```bash
git add -A
git commit -m "test: full behave + pytest suite green" --allow-empty
```

---

## Task 22: Config file loading

**Files:**
- Modify: `src/generic_scraper/config.py`
- Test: `tests/unit/test_config_file.py`

**Interfaces:**
- Consumes: `ScraperType`, `PyYAML`.
- Produces: `ScraperType.from_file(path: str | Path) -> ScraperType` — reads a YAML file whose top-level keys match `ScraperType` field names, applying the same `"true"/"false"`/digit-string coercion helper factored out of Task 11's `common_steps.py` into a shared `src/generic_scraper/_coerce.py` (or kept simple since YAML already types `true`/`123` natively — builder's call whether coercion is needed at all for YAML).

- [ ] **Step 1: Write failing tests**

```python
def test_from_file_loads_yaml_config(tmp_path):
    p = tmp_path / "scraper.yaml"
    p.write_text("scraper_engine: playwright\nbrowser_type: firefox\n")
    cfg = ScraperType.from_file(p)
    assert cfg.scraper_engine == "playwright"
    assert cfg.browser_type == "firefox"

def test_from_file_applies_defaults_for_omitted_fields(tmp_path):
    p = tmp_path / "scraper.yaml"
    p.write_text("processing_type: lxml\n")
    cfg = ScraperType.from_file(p)
    assert cfg.scraper_engine == "requests"
    assert cfg.processing_type == "lxml"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_config_file.py -v`
Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement `ScraperType.from_file`** using `yaml.safe_load`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_config_file.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/generic_scraper/config.py tests/unit/test_config_file.py
git commit -m "feat: load ScraperType from a YAML config file"
```

---

## Task 23: Logging/observability

**Files:**
- Create: `src/generic_scraper/logging_config.py`
- Modify: `src/generic_scraper/scraper.py`
- Test: `tests/unit/test_logging.py`

**Interfaces:**
- Consumes: stdlib `logging`, `Scraper`.
- Produces: `def configure_logging(level: int = logging.INFO) -> None` setting up a `"generic_scraper"` logger with a stream handler. `Scraper` logs (via `logging.getLogger("generic_scraper")`) one INFO line on successful init with the chosen engine, one WARNING line per fallback, one WARNING line per retry attempt, and one INFO line per successful fetch with the URL and processor used.

- [ ] **Step 1: Write failing tests** using `caplog` (pytest fixture):

```python
def test_scraper_logs_engine_choice_on_init(caplog):
    with caplog.at_level(logging.INFO, logger="generic_scraper"):
        Scraper(ScraperType())
    assert any("requests" in r.message for r in caplog.records)

def test_scraper_logs_fallback(caplog, monkeypatch):
    monkeypatch.setattr(PlaywrightEngine, "is_available", lambda self: False)
    with caplog.at_level(logging.WARNING, logger="generic_scraper"):
        Scraper(ScraperType(scraper_engine="playwright"))
    assert any("fallback" in r.message.lower() for r in caplog.records)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_logging.py -v`
Expected: FAIL (no log records).

- [ ] **Step 3: Add logging calls to `Scraper`** at the points described; implement `configure_logging` for CLI/application use (not required by the tests, which use `caplog` directly against the named logger).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_logging.py -v`
Expected: PASS

- [ ] **Step 5: Confirm the full suite is still green**

Run: `behave && pytest tests/`
Expected: all green (logging must not change any observable behavior feature steps assert on).

- [ ] **Step 6: Commit**

```bash
git add src/generic_scraper/logging_config.py src/generic_scraper/scraper.py tests/unit/test_logging.py
git commit -m "feat: logging for engine selection, fallback, retry, fetch"
```

---

## Task 24: CLI entry point

**Files:**
- Create: `src/generic_scraper/cli.py`
- Modify: `pyproject.toml` (add `[project.scripts] generic-scraper = "generic_scraper.cli:main"`)
- Test: `tests/unit/test_cli.py`

**Interfaces:**
- Consumes: `ScraperType`, `ScraperType.from_file`, `Scraper`, `logging_config.configure_logging`.
- Produces: `def build_parser() -> argparse.ArgumentParser` with a `fetch` subcommand taking `url` (positional), `--config` (path to YAML, optional), `--engine`, `--processing-type` (optional overrides applied on top of a loaded/default `ScraperType`). `def main(argv: list[str] | None = None) -> int` — parses args, builds `ScraperType`, runs `Scraper(...).fetch(url)`, prints the parsed title to stdout, returns `0` on success and `1` on any `ScraperError`.

- [ ] **Step 1: Write failing tests**

```python
def test_main_fetches_and_prints_title(monkeypatch, capsys):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>CLI Title</title></html>")
    exit_code = main(["fetch", "https://example.com"])
    assert exit_code == 0
    assert "CLI Title" in capsys.readouterr().out

def test_main_returns_1_on_unsupported_engine(capsys):
    exit_code = main(["fetch", "https://example.com", "--engine", "not-real"])
    assert exit_code == 1

def test_main_applies_config_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(RequestsEngine, "fetch", lambda self, url: "<html><title>From File</title></html>")
    p = tmp_path / "cfg.yaml"
    p.write_text("processing_type: lxml\n")
    exit_code = main(["fetch", "https://example.com", "--config", str(p)])
    assert exit_code == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_cli.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `build_parser` and `main`** as described.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Reinstall editable and smoke-test the real entry point**

Run: `pip install -e . && generic-scraper fetch https://example.com --engine requests` (this one real invocation is expected to make a real network call — fine as a manual smoke test, not part of the automated suite)
Expected: prints a title or a clear error, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add src/generic_scraper/cli.py pyproject.toml tests/unit/test_cli.py
git commit -m "feat: CLI entry point"
```

---

## Task 25: README and final full-suite verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`** covering: what the package does, install instructions (`pip install -e ".[dev,browsers]"`), how to run `behave` and `pytest`, CLI usage example, a one-paragraph note that the distributed job layer (feature 07) is simulated in-process and not a real cluster integration.
- [ ] **Step 2: Run the full suite one final time**

Run: `behave && pytest tests/ -v`
Expected: 8 features / 31 scenarios passed in behave; all unit tests passed in pytest.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README and final verification"
```
