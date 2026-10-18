# generic-scraper

A configuration-driven, pluggable web scraper for Python. `Scraper` and
`ScraperType` let you fetch a page with a chosen fetch engine, parse the
result with a chosen parser, and configure retries, fallbacks, proxies and
headers — all driven by a simple config object or a YAML file.

The behavior of the package is specified and verified by 8 Gherkin feature
files (31 scenarios) under `features/`, covering:

1. Scraper initialization and defaults
2. Browser/engine configuration
3. Defaults and fallback behavior
4. Proxy and header support
5. Processing (parser) types
6. End-to-end fetch + parse
7. Distributed execution and artifacts (**simulated** — see note below)
8. Error handling and retries

## Features

- **Pluggable fetch engines**: `requests`, `playwright`, `selenium` — selected
  by name via `ScraperType.scraper_engine`. Engine fallback is supported if a
  preferred engine is unavailable or fails.
- **Pluggable parsers**: `beautifulsoup`, `lxml`, `html.parser`, `regex` —
  selected via `ScraperType.processing_type`.
- **Proxy and custom header support** for outgoing requests.
- **Retry logic** with configurable attempts/backoff, and engine fallback on
  failure.
- **YAML configuration loading**: build a `ScraperType` from a config file
  with `ScraperType.from_file(path)`.
- **Logging**: engine selection, fallback, retry attempts, and fetch
  activity are logged via `generic_scraper.logging_config`.
- **CLI**: a `generic-scraper` console script for ad-hoc fetches.
- **Simulated distributed job layer**: an in-process orchestrator/worker-node
  simulation (`generic_scraper.distributed`) used to exercise feature 07's
  distributed-execution-and-artifacts scenarios.

## Installation

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode plus `behave` and `pytest` for
running the test suites.

The `browsers` extra (`playwright`, `selenium`) is **optional** and is not
required to run the test suite — in both `behave` and `pytest`, the
playwright/selenium engines are mocked at the engine boundary, so no real
browser binaries or drivers need to be installed. Install it only if you
intend to actually drive a real browser at runtime:

```bash
pip install -e ".[dev,browsers]"
```

## Running the tests

Run the Gherkin behavioral suite:

```bash
behave
```

Expected: 8 features, 31 scenarios, all passed.

Run the unit test suite:

```bash
pytest tests/ -v
```

Expected: all unit tests passed.

## CLI usage

Once installed, the `generic-scraper` command is available:

```bash
generic-scraper fetch https://example.com --engine requests --processing-type beautifulsoup
```

Optional flags:

- `--config path/to/config.yaml` — load a `ScraperType` from a YAML file.
- `--engine <name>` — override the fetch engine (`requests`, `playwright`,
  `selenium`).
- `--processing-type <name>` — override the parser
  (`beautifulsoup`, `lxml`, `html.parser`, `regex`).

`--engine`/`--processing-type` override whatever is loaded from `--config`.
The command fetches the URL and prints the parsed document's title.

## Note on the distributed job layer

The "distributed execution" functionality (`generic_scraper.distributed`,
exercised by feature 07) is an **in-process simulation** of a job
orchestrator and worker nodes. It models job submission, node assignment,
execution, and artifact collection entirely within a single Python process
for testing and demonstration purposes. It is **not** an integration with
any real distributed system, job queue, or cluster orchestrator (e.g. no
Celery, Kubernetes, Ray, etc. is involved), and it should not be treated as
production-ready distributed infrastructure.
