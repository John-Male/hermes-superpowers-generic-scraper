from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ParsedDocument:
    raw_html: str
    title: str | None = None


class Parser(Protocol):
    def parse(self, html: str) -> ParsedDocument:
        ...
