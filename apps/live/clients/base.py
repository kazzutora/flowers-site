"""tech.md §4.3 — frozen ABC signature."""

from __future__ import annotations

from abc import ABC, abstractmethod

from apps.live.clients.dto import HealthDTO, LiveStreamDTO, PlaybackDTO


class StreamProvider(ABC):
    @abstractmethod
    def get_playback(self, stream: LiveStreamDTO) -> PlaybackDTO: ...

    @abstractmethod
    def check_health(self, stream: LiveStreamDTO) -> HealthDTO: ...

    @abstractmethod
    def grab_snapshot(self, stream: LiveStreamDTO) -> bytes | None: ...
