"""FakeStreamProvider — tech.md §4.3, §9.1, S0.7. Serves the looped demo
clip in ``static/dev/`` so the camera works end-to-end with zero
hardware; can also simulate a hard failure or an offline camera by flag,
which is what every camera error-path test in stage 2 is built against.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings

from apps.live.clients.base import StreamProvider
from apps.live.clients.dto import HealthDTO, LiveStreamDTO, PlaybackDTO
from apps.live.clients.errors import StreamProviderError

DEMO_VIDEO_PATH = "dev/live-demo.mp4"
DEMO_POSTER_PATH = "dev/live-demo-poster.webp"


class FakeStreamProvider(StreamProvider):
    def __init__(self, *, fail: bool = False, offline: bool = False) -> None:
        self.fail = fail
        self.offline = offline

    def get_playback(self, stream: LiveStreamDTO) -> PlaybackDTO:
        if self.fail:
            raise StreamProviderError("fake stream provider: get_playback failed")
        base_url = settings.SITE_URL.rstrip("/")
        return PlaybackDTO(
            kind="hls",
            url=f"{base_url}/static/{DEMO_VIDEO_PATH}",
            poster_url=f"{base_url}/static/{DEMO_POSTER_PATH}",
            is_live=not self.offline,
            latency_hint_s=2,
        )

    def check_health(self, stream: LiveStreamDTO) -> HealthDTO:
        if self.fail:
            raise StreamProviderError("fake stream provider: check_health failed")
        return HealthDTO(
            status="offline" if self.offline else "online",
            checked_at=datetime.now(UTC),
        )

    def grab_snapshot(self, stream: LiveStreamDTO) -> bytes | None:
        if self.fail:
            raise StreamProviderError("fake stream provider: grab_snapshot failed")
        if self.offline:
            return None
        poster_path = Path(settings.BASE_DIR) / "static" / DEMO_POSTER_PATH
        return poster_path.read_bytes()
