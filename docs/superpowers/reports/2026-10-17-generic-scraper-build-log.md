# Generic Scraper — Build Log and Review Summary

> Reconstructed after the fact from the session record. The original
> working files (`.superpowers/sdd/2026-10-17-generic-scraper/` — task
> briefs, per-task implementer reports, reviewer write-ups, and the
> execution ledger) were deleted at the end of the run per the
> subagent-driven-development workflow's close-out step, once the final
> whole-branch review came back clean. This document recreates their
> substance for the repo's permanent record.
>
> Plan: `docs/superpowers/plans/2026-10-17-generic-scraper.md`
> Design doc: `docs/superpowers/specs/2026-10-17-generic-scraper-design.md`

## Process

Implemented via Subagent-Driven Development: a fresh implementer subagent
per task (TDD — write failing test, confirm RED, implement, confirm
GREEN, commit), a fresh reviewer subagent per task (spec compliance +
code quality), a fix loop for any Critical/Important finding (fix →
scoped re-review), and one final whole-branch review at the end with one
fix wave. All work landed directly on `main` with the repo owner's
explicit consent (no feature branch/worktree isolation used).

## Pre-flight scan (before Task 1)

Two naming gaps found between task interfaces, ruled before execution began:

- **`Scraper.config` attribute**: Task 9's spec didn't name an attribute
  for the stored `ScraperType`, but Tasks 12/15 needed to read
  `scraper.config.browser_type` / `.processing_type`. **Ruling:**
  `Scraper.__init__` stores it as `self.config`.
- **`RequestsEngine.session` attribute**: Task 6's spec described session
  configuration behavior but never named the attribute; Task 14 needed
  `engine.session.proxies` / `.headers`. **Ruling:** stored as
  `self.session`.

## Task-by-task outcomes

| Task | What it built | Review outcome |
|---|---|---|
| 1 | Project scaffolding (src/ layout, pyproject.toml, behave.ini, pytest) | Approved. `[browsers]` extras install failed on this host (greenlet needs MSVC Build Tools) — noted as environment limitation, not a defect; `[dev]`-only install verified clean. |
| 2 | Error hierarchy (`ScraperError`, `UnsupportedScraperEngineError`, `EngineUnavailableError`, `EngineStartError`) | Approved. `EngineStartError` made a subclass of `EngineUnavailableError` (builder's call) — noted as load-bearing for later `except` clauses. |
| 3 | `ScraperType` config dataclass | Approved, no findings. |
| 4 | Parser abstraction (beautifulsoup/lxml/html.parser/regex) | Approved. Noted: regex parser doesn't HTML-entity-decode titles while the others do — accepted as non-blocking, no feature scenario exercises entity-bearing titles. |
| 5 | Engine interface + registry (`register_engine`/`get_engine_class`) | Approved. Minor: test registered a `DummyEngine` into the real module-level registry instead of an isolated instance — deferred, low risk. |
| 6 | `RequestsEngine` (proxy + header support) | Approved, no findings. `self.session` ruling confirmed in code. |
| 7 | `PlaywrightEngine`/`SeleniumEngine` (mocked) | **Needs fixes → fixed.** `engines/__init__.py` never imported the new engine modules, so `get_engine_class("playwright"/"selenium")` raised `UnsupportedScraperEngineError` on a clean import — nothing ever triggered their `register_engine()` calls. Fixed by mirroring Task 6's eager-import pattern; added a subprocess-based regression test proving a clean import populates the registry. |
| 8 | Retry with exponential backoff | Approved (reviewer flagged a self-contradictory "Important but non-blocking" finding re: test coverage on exact call counts — ruled as deferred-minor since the reviewer's own verdict was Approved and the underlying logic was independently confirmed correct). Noted: `attempts<=0` raised a raw `AssertionError` — flagged as out-of-scope at the time since no caller passed untrusted values yet (later became a real bug, see Final Review). |
| 9 | `Scraper.__init__` (engine selection + fallback) | Approved. Both controller rulings (`self.config`, catching `EngineUnavailableError`) verified directly in code. Reviewer confirmed single-hop fallback is correctly scoped — no feature scenario needs multi-hop chaining. |
| 10 | `Scraper.fetch` (retry + parse) | Approved, no findings. |
| 11 | Behave world setup + shared steps (feature 01) | Approved. Two judgment calls: `context.scraper_config` used instead of `context.config` (behave reserves `config` on its own `Context`); `"default scraper configuration exists"` seeds `browser_type="chrome"` and `environment.py`'s `before_all`/`after_all` globally patches the mocked browser engines' default launcher/availability to "always succeeds" — confirmed not to contaminate feature 03. **Ruling carried forward:** any later per-scenario override of that global patch (e.g. Task 13's "engine not available" step) must use `context.add_cleanup` to avoid leaking across scenarios. |
| 12 | Feature 02 — browser configuration steps | **Needs fixes → fixed.** The `browser_type` assertion was tautological (compared the test's own input config back to itself); the mocked launcher didn't record its argument. Fixed by making the launcher record calls and asserting against the recorded call. |
| 13 | Feature 03 — defaults and fallback steps | Approved. `context.add_cleanup` ruling verified directly in code (patch + cleanup registered unconditionally); confirmed no leakage into features 01/02 on re-run. |
| 14 | Feature 04 — proxy and headers steps | Approved, no findings. Correctly asserted against the real `engine.session.proxies`/`.headers`, applying the Task 12 lesson. |
| 15 | Feature 05 — processing types steps | Approved. Correctly asserted `isinstance(get_parser(processor), expected_class)` against real parser classes rather than echoing the input string. |
| 16 | Feature 06 — end-to-end fetch/parse steps | Approved, no findings. `context.add_cleanup` used correctly for the fetch monkeypatch; canned HTML confirmed to flow through the real retry+parse pipeline. |
| 17 | Feature 08 — error handling and retries steps | Approved. All 3 controller requirements verified: a real call-counter for the retry-count assertion (not just the final exception type), exact exception class-name check for init failure, `context.add_cleanup` for monkeypatches. Modified the shared `common_steps.py`'s "When I initialize the Scraper" step to capture init exceptions — confirmed backward-compatible via full suite re-run. |
| 18 | Simulated node registry (`Node`, `NodeRegistry`, `default_registry`) | Approved. `find_matching_node` confirmed to genuinely filter on GPU/memory/browser simultaneously and return `None` on no match — directly defusing the design doc's named "always return first node" anti-goal risk. |
| 19 | Simulated artifact store + job orchestrator | Approved. Anti-goal requirements verified live: distinct worker IDs per shard, real per-shard artifact uploads, `schedule_with_constraints` raises `NoSuitableNodeError` (not `None`) delegating to the real registry. Minor: unused `Scraper(config)` construction in `schedule()` (dead code, not a correctness issue). |
| 20 | Feature 07 — distributed execution steps (last feature file) | Approved. Brought the full behave suite to 8/8 features passing. Added one additive `@given` alias to shared `common_steps.py` for feature 07's slightly different Gherkin phrasing — confirmed purely additive. |
| 21 | Full-suite checkpoint | Checkpoint only. Controller independently re-ran `behave` + `pytest`: 8 features / 31 scenarios / 145 steps, 48 pytest, all green. |
| 22 | YAML config file loading (`ScraperType.from_file`) | **Needs fixes → fixed.** Unrecognized/misspelled YAML keys were silently dropped instead of raising — a user typo (e.g. `scraper_enginee`) would silently fall back to defaults with no warning. Fixed by raising `ValueError` listing the unrecognized key(s). |
| 23 | Logging (engine selection, fallback, retry, fetch) | Approved. Control-flow purity independently verified (one lambda→named-closure refactor in `fetch`, confirmed behavior-preserving). pytest and full behave suite both confirmed unchanged. |
| 24 | CLI entry point (`generic-scraper`) | **Needs fixes → fixed.** `main()` only caught `ScraperError`, but `ScraperType.from_file`'s unrecognized-key error is a plain `ValueError` — a malformed `--config` file crashed the CLI with a raw traceback instead of returning exit code 1. Fixed by broadening the `except` clause. |
| 25 | README + final verification | Complete. README documents the package, install, test commands, CLI usage, and explicitly notes the distributed layer is simulated, not real infrastructure. Final counts independently reproduced: 8 features / 31 scenarios / 145 steps, 59 pytest. |

## Final whole-branch review

One additional **Important** finding surfaced only at the whole-branch level,
not visible to any single task's scoped review: `retry_with_backoff`
crashed with a bare `AssertionError` on `attempts <= 0`, and — now that
Tasks 22 (config file) and 24 (CLI) existed — this was externally
reachable: a user's `retry_attempts: 0` in a YAML config, loaded via
`--config`, would crash the CLI with a raw traceback and no clean exit
code, since `main()`'s exception handling didn't catch `AssertionError`.
This invalidated Task 8's original "not exercised by any caller" deferral.

**Fix:** validated `retry_attempts >= 1` in `ScraperType.__post_init__`
(the earliest point, catching both direct construction and `from_file`),
plus a defense-in-depth `ValueError` guard in `retry_with_backoff` itself.
Verified: happy path (`attempts >= 1`) completely unchanged; the CLI's
existing `except (ScraperError, ValueError)` now genuinely catches the new
error end-to-end and returns exit code 1. Scoped re-review: **PASS**, no
new breakage.

Items triaged at the final review and confirmed non-blocking (not fixed):

- CLI `--processing-type` validation — already covered by the existing
  exception handling via `get_parser()`'s `ValueError`.
- Node registry's combined-3-constraint test coverage gap — production
  logic applies all three predicates unconditionally regardless, so the
  gap is a coverage nicety, not a correctness risk.
- `pyproject.toml`'s `requires-python = ">=3.9"` vs. the plan's "Python
  3.11+" prose — harmless since `from __future__ import annotations` is
  used throughout.
- Dead `Scraper()` construction in `Orchestrator.schedule()` (Task 19).
- `Engine` Protocol being `@runtime_checkable` with a non-callable
  attribute — theoretical, nothing in the codebase does `isinstance`
  checks against it.
- Regex parser's non-entity-decoding title extraction (Task 4) — already
  accepted as non-blocking, no scenario exercises it.

## Final state

- `behave`: 8 features, 31 scenarios, 145 steps — all passing.
- `pytest`: 64 tests — all passing.
- 33 commits on `main`, pushed to
  https://github.com/John-Male/hermes-superpowers-generic-scraper
