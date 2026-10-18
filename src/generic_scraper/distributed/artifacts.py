"""Simulated in-memory artifact store for the distributed job layer."""
from __future__ import annotations


class ArtifactStore:
    """In-memory, dict-backed stand-in for a real artifact/object store."""

    def __init__(self) -> None:
        self._artifacts: dict[str, bytes | str] = {}

    def upload(self, name: str, data: bytes | str) -> None:
        self._artifacts[name] = data

    def exists(self, name: str) -> bool:
        return name in self._artifacts

    def get(self, name: str) -> bytes | str:
        return self._artifacts[name]
