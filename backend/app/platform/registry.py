from __future__ import annotations

from collections.abc import Iterable

from .base import PlatformSourceAdapter


class PlatformSourceRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, PlatformSourceAdapter] = {}

    def register(self, adapter: PlatformSourceAdapter) -> None:
        self._adapters[adapter.source_system] = adapter

    def get(self, source_system: str) -> PlatformSourceAdapter | None:
        return self._adapters.get(source_system)

    def all(self) -> Iterable[PlatformSourceAdapter]:
        return self._adapters.values()


registry = PlatformSourceRegistry()

