"""Simulated node registry for the distributed job layer.

This module models a simple in-memory registry of compute "nodes" with
resource/affinity attributes (GPU availability, memory, supported
browsers), and provides matching against job requirements. It is a pure
dataclass + registry with no dependency on the scraping engine/parsers.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    node_id: str
    has_gpu: bool
    memory_gb: int
    browsers: frozenset[str] = field(default_factory=frozenset)


class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: list[Node] = []

    def register(self, node: Node) -> None:
        self._nodes.append(node)

    def find_matching_node(
        self,
        *,
        requires_gpu: bool = False,
        min_memory_gb: int = 0,
        browser: str | None = None,
    ) -> Node | None:
        for node in self._nodes:
            if requires_gpu and not node.has_gpu:
                continue
            if node.memory_gb < min_memory_gb:
                continue
            if browser is not None and browser not in node.browsers:
                continue
            return node
        return None


def default_registry() -> NodeRegistry:
    registry = NodeRegistry()
    registry.register(
        Node("node-1", has_gpu=False, memory_gb=1, browsers=frozenset({"chrome"}))
    )
    registry.register(
        Node(
            "node-2",
            has_gpu=False,
            memory_gb=4,
            browsers=frozenset({"chrome", "firefox"}),
        )
    )
    registry.register(
        Node("node-3", has_gpu=True, memory_gb=8, browsers=frozenset())
    )
    return registry
