"""DTOs for the StreamProvider boundary (tech.md §4.3, §9.1).

``PlaybackDTO`` is copied verbatim from tech.md §4.3 — frozen, field for
field. ``LiveStreamDTO`` and ``HealthDTO`` are referenced there by type
name only (unlike ``PlaybackDTO`` they get no field table); their fields
here are derived directly from the already-frozen ``LiveStream`` model
columns (tech.md §4.3: ``store``, ``provider``, ``source_ref``, ``title``,
``is_enabled``, ``aspect_ratio``, ``has_audio``, ``schedule``,
``health_status``) with no new business field introduced. Flagged as a
CONTRACT GAP in the S0.7 PR description — revisit once stage 2 (live)
freezes the real shape alongside the ``LiveStream`` model itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl


class PlaybackDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["hls", "webrtc", "iframe"]
    url: HttpUrl
    poster_url: HttpUrl | None
    is_live: bool
    latency_hint_s: int


class LiveStreamDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_slug: str
    provider: str
    source_ref: str
    title: str
    is_enabled: bool
    aspect_ratio: str
    has_audio: bool
    schedule: dict[str, list[str] | None]
    health_status: Literal["online", "offline", "unknown"]


class HealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["online", "offline", "unknown"]
    checked_at: datetime
