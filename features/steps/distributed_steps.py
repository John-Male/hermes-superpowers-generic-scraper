"""Step definitions for `features/07_distributed_execution_and_artifacts.feature`.

These steps drive the simulated distributed job layer: `Orchestrator`
scheduling shards across a `default_registry()` of nodes and uploading
parsed results to an in-memory `ArtifactStore`, plus the resource/affinity
matching path (`schedule_with_constraints`).
"""

from __future__ import annotations

from behave import given, when, then

from generic_scraper.config import ScraperType
from generic_scraper.distributed.artifacts import ArtifactStore
from generic_scraper.distributed.nodes import default_registry
from generic_scraper.distributed.orchestrator import Orchestrator
from generic_scraper.errors import NoSuitableNodeError


def _parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _parse_memory_gb(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits)


@given("the job is configured to run with {shards:d} parallel shards")
def step_configure_shards(context, shards):
    context.shards = shards


@when("the orchestrator schedules the job")
def step_schedule_job(context):
    context.scraper_config = ScraperType(**context.config_kwargs)
    context.artifact_store = ArtifactStore()
    context.orchestrator = Orchestrator(default_registry(), context.artifact_store)

    if getattr(context, "shards", None) is not None:
        context.shard_results = context.orchestrator.schedule(
            context.scraper_config, context.shards
        )
    else:
        context.constraint_error = None
        try:
            context.scheduled_node = context.orchestrator.schedule_with_constraints(
                requires_gpu=context.requires_gpu,
                min_memory_gb=context.min_memory_gb,
                browser=context.config_kwargs.get("browser_type"),
            )
        except NoSuitableNodeError as exc:
            context.scheduled_node = None
            context.constraint_error = exc


@then("the job should run on {shards:d} distinct worker nodes")
def step_distinct_worker_nodes(context, shards):
    assert context.shard_results is not None, "Orchestrator was not scheduled"
    worker_ids = {result.worker_id for result in context.shard_results}
    assert len(worker_ids) == shards, (
        f"Expected {shards} distinct worker nodes, got {len(worker_ids)}: {worker_ids}"
    )


@then("each worker should produce a parsed artifact")
def step_each_worker_produces_artifact(context):
    assert context.shard_results, "No shard results to check"
    for result in context.shard_results:
        assert context.artifact_store.exists(result.artifact_name), (
            f"Expected artifact {result.artifact_name!r} to exist in the artifact store"
        )


@given('a worker produced "{artifact}"')
def step_worker_produced_artifact(context, artifact):
    context.artifact_store = ArtifactStore()
    context.artifact_name = artifact
    context.artifact_uploaded = False


@when("the worker finishes the shard")
def step_worker_finishes_shard(context):
    context.artifact_store.upload(context.artifact_name, "parsed-result-payload")
    context.artifact_uploaded = True


@then('the artifact "{artifact}" should be uploaded to the job artifact store')
def step_artifact_uploaded(context, artifact):
    assert context.artifact_uploaded, "Worker did not finish the shard"
    assert context.artifact_store.exists(artifact), (
        f"Expected artifact {artifact!r} to be uploaded to the job artifact store"
    )


@given("the job requests GPU {gpu_flag} and memory {memory}")
def step_job_requests_resources(context, gpu_flag, memory):
    context.shards = None
    context.requires_gpu = _parse_bool(gpu_flag)
    context.min_memory_gb = _parse_memory_gb(memory)


@then("the job should be placed on a node that satisfies the resource constraints")
def step_node_satisfies_constraints(context):
    assert context.constraint_error is None, (
        f"Expected a suitable node, but scheduling raised: {context.constraint_error!r}"
    )
    assert context.scheduled_node is not None, "No node was scheduled"
    if context.requires_gpu:
        assert context.scheduled_node.has_gpu
    assert context.scheduled_node.memory_gb >= context.min_memory_gb
    browser = context.config_kwargs.get("browser_type")
    if browser is not None:
        assert browser in context.scheduled_node.browsers
