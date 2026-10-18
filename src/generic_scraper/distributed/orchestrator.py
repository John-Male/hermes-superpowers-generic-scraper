"""Simulated job orchestrator for the distributed job layer.

Schedules shards onto simulated workers, drives each shard's HTML through a
`Scraper`-configured parser (no real network access), and uploads a parsed
result artifact per worker. Also supports matching a single job's
constraints against the node registry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from generic_scraper.config import ScraperType
from generic_scraper.distributed.artifacts import ArtifactStore
from generic_scraper.distributed.nodes import Node, NodeRegistry
from generic_scraper.errors import NoSuitableNodeError
from generic_scraper.parsers import get_parser
from generic_scraper.scraper import Scraper

_CANNED_HTML = "<html><head><title>Simulated Page</title></head><body></body></html>"


@dataclass
class ShardResult:
    worker_id: str
    artifact_name: str


class Orchestrator:
    def __init__(self, registry: NodeRegistry, artifact_store: ArtifactStore) -> None:
        self.registry = registry
        self.artifact_store = artifact_store

    def schedule(
        self,
        config: ScraperType,
        shards: int,
        fetch_fn: Callable[[], str] | None = None,
        ) -> list[ShardResult]:
        """Assign each shard a distinct simulated worker and parse/upload its result."""
        fetch = fetch_fn or (lambda: _CANNED_HTML)
        scraper = Scraper(config)
        parser = get_parser(config.processing_type)

        results: list[ShardResult] = []
        for i in range(shards):
            worker_id = f"worker-{i}"
            html = fetch()
            parsed = parser.parse(html)
            artifact_name = f"{worker_id}/parsed_result.json"
            payload = json.dumps(
                {"raw_html": parsed.raw_html, "title": parsed.title}
            )
            self.artifact_store.upload(artifact_name, payload)
            results.append(ShardResult(worker_id=worker_id, artifact_name=artifact_name))
        # scraper is constructed to validate engine selection for this config;
        # fetching here is simulated via `fetch_fn`, never a real network call.
        del scraper
        return results

    def schedule_with_constraints(
        self,
        *,
        requires_gpu: bool,
        min_memory_gb: int,
        browser: str | None,
    ) -> Node:
        node = self.registry.find_matching_node(
            requires_gpu=requires_gpu,
            min_memory_gb=min_memory_gb,
            browser=browser,
        )
        if node is None:
            raise NoSuitableNodeError(
                f"No node satisfies requires_gpu={requires_gpu}, "
                f"min_memory_gb={min_memory_gb}, browser={browser!r}"
            )
        return node
