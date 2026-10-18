# Generic Scraper — Design

## Intent and why

A Python package implementing a configurable `Scraper`, driven by a
`ScraperType` configuration object, that can fetch a page with one of
several interchangeable engines and parse it with one of several
interchangeable HTML parsers. The behavior is fully specified by the
Gherkin feature files in `features/` (8 files, originally written
against a "Swarm Forge" test harness; all Swarm Forge branding has been
removed by the project owner and no real Swarm Forge integration exists
or is planned). The purpose of this repo is to make every scenario in
those 8 feature files pass against real, working code — this is a
demonstration/exercise repo for going from a BDD spec to an implemented,
tested package.

## Goals

- Implement `ScraperType` (config) and `Scraper` (behavior) so that all
  scenarios across the 8 feature files pass as executable BDD tests.
- Support three fetch engines: `requests`, `playwright`, `selenium`,
  defaulting to `requests` when unconfigured.
- Support `browser_type` (`chrome`/`firefox`) for the two browser-based
  engines.
- Support proxy configuration (`proxy_url`, `proxy_port`) and an optional
  auth header pass-through (`proxy_pass_key`/`proxy_pass_val`).
- Support four parsers: `beautifulsoup`, `lxml`, `html.parser`, `regex`,
  producing a parsed-document object that exposes at least the page
  title.
- Resilience: configurable retry with exponential backoff on transient
  fetch errors; automatic fallback to a configured `secondary` engine, or
  to `requests` as the universal fallback, when the primary engine fails
  to start or is unavailable; a typed `UnsupportedScraperEngineError`
  (and similar descriptive errors) when no usable engine exists.
- A **simulated** distributed job layer (feature file 07) implemented
  in-process (no real network, no real cluster) that can:
  - fan a job out across N simulated worker "shards", each producing a
    parsed artifact,
  - upload/collect those artifacts into a simulated artifact store,
  - register simulated worker nodes with resource attributes (GPU
    boolean, memory) and place jobs only on nodes satisfying a job's
    requested constraints and browser/affinity needs.
- Additional scope beyond the 8 feature files, requested by the owner:
  - a CLI entry point to run the scraper from the command line,
  - loading `ScraperType` configuration from a config file (e.g.
    YAML/JSON/TOML — builder's call),
  - basic logging/observability (structured log lines for fetch
    attempts, retries, fallbacks, parse results, and simulated job
    scheduling/artifact events).

## Non-goals

- No real browser automation infrastructure beyond what `playwright`/
  `selenium` themselves provide locally (no remote Selenium grid, no
  real headless farm).
- No real distributed orchestrator, real worker machines, real network
  artifact storage, or integration with any actual job-scheduling
  product. Feature 07 is simulated/in-process only.
- No real proxy server or real external network dependency is required
  for the test suite to pass — proxy and fetch behavior should be
  testable via mocks/fakes, not live network calls.
- No authentication/security hardening beyond passing through the
  configured proxy auth header verbatim.

## Anti-goals

(Things that would make this a failure even if "technically working")

- A test suite that only passes because steps are stubbed to always
  succeed, rather than exercising real (mocked-at-the-boundary) logic.
- Hidden, undocumented defaults that don't match what the feature files
  specify (e.g. the default engine must genuinely be `requests`, not
  just claimed to be).
- A "simulated" job layer that is a no-op — it must actually shard,
  actually enforce resource/affinity constraints (reject placements that
  don't satisfy them), and actually track artifacts per shard.

## Constraints

- Language: Python (owner-specified).
- Repo location:
  `C:\Users\johnm\hermes_real_skill_test\hermes-superpowers-generic-scraper`
- The 8 feature files in `features/` are the spec of record for engine,
  browser, defaults/fallback, proxy/headers, processing types, e2e
  fetch+parse, distributed/artifacts, and error-handling/retry behavior.
  They should not be rewritten to fit the implementation; the
  implementation must fit them.
- No real network calls in tests; engine/browser/HTTP interactions must
  be fake-able/mockable at the boundary so the suite runs offline and
  deterministically.

## Decided (owner's calls, as decided)

- Stack: Python.
- Repo path: as above, pre-created with git initialized.
- Swarm Forge: not used at all; all references removed from feature
  files; feature 07's behavior is simulated in-process rather than
  dropped.
- Scope extension: CLI entry point, file-based config loading, and
  logging/observability are in scope, in addition to the 8 feature
  files.
- Browser/engine testing: Playwright and Selenium are mocked at the
  engine boundary. The test suite does not launch real local browsers,
  install browser binaries, or depend on chromedriver/geckodriver;
  "launching chrome/firefox" is verified by asserting the Scraper
  selected and configured the right engine/browser combination against
  a fake/mock engine interface, not a real browser window.
- Engine availability/failure detection (builder's call, settled): a
  real capability-check seam is used in production code (e.g. probing
  whether the engine's package/driver is importable/usable), but it is
  injectable so tests can force "unavailable"/"fails to start" results
  deterministically without depending on real environment conditions.
- Worker-flavored step wording ("on a Swarm Forge worker" / "on a worker
  node" vs. plain "I initialize the Scraper") (builder's call, settled):
  this is leftover phrasing from the Swarm Forge branding removal with
  no intended behavioral difference. All such steps share the same step
  definitions; no per-node/per-environment concept is introduced into
  the Scraper API because of this wording.

## Left to the builder

- BDD test runner choice (default suggestion: `behave`, since it's the
  standard runner for `.feature` files with no step definitions yet, no
  existing choice to conflict with). `pytest-bdd` is an acceptable
  alternative if there's a reason to prefer it.
- Package layout (e.g. `src/` layout vs flat), dependency management
  (`pyproject.toml` recommended), and packaging metadata.
- Internal architecture: how the engine/parser abstractions are
  structured (e.g. strategy classes, registry/factory pattern), as long
  as the public behavior matches the feature files.
- Exact exception hierarchy beyond the one named error
  (`UnsupportedScraperEngineError`) referenced in the spec.
- Retry/backoff concrete defaults (base delay, multiplier, jitter) where
  the feature files only specify attempt counts.
- Config file format for the new file-based config loading (YAML/JSON/
  TOML) and its on-disk schema.
- CLI framework choice (e.g. `argparse`, `click`, `typer`) and its exact
  command/flag surface.
- Logging framework/format (stdlib `logging` vs structured logging lib)
  and exact log line shapes.
- Design of the simulated node registry and artifact store (in-memory
  vs on-disk under e.g. `.artifacts/`), as long as scenario 07's
  assertions (distinct nodes per shard, artifact present in the store,
  placement respects constraints) are genuinely enforced.
