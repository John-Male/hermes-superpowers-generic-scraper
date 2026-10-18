from __future__ import annotations

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.distributed.artifacts import ArtifactStore
from generic_scraper.distributed.nodes import default_registry
from generic_scraper.distributed.orchestrator import Orchestrator
from generic_scraper.errors import NoSuitableNodeError


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
