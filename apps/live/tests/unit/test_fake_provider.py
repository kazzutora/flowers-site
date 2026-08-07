from pathlib import Path

import pytest
from django.conf import settings

from apps.live.clients.dto import LiveStreamDTO
from apps.live.clients.errors import StreamProviderError
from apps.live.clients.fake import DEMO_POSTER_PATH, DEMO_VIDEO_PATH, FakeStreamProvider

STREAM = LiveStreamDTO(
    store_slug="centr",
    provider="fake",
    source_ref="centr-demo",
    title="Наживо: зал на Хрещатику",
    is_enabled=True,
    aspect_ratio="16:9",
    has_audio=False,
    schedule={"mon": ["09:00", "20:00"]},
    health_status="online",
)


def test_demo_video_file_exists_and_is_playable() -> None:
    """S0.7 acceptance: the test clip lives in static/dev/ and plays
    locally without a single piece of hardware."""
    video_path = Path(settings.BASE_DIR) / "static" / DEMO_VIDEO_PATH
    assert video_path.exists()
    assert video_path.stat().st_size > 0
    # Minimal MP4 container sanity check: an "ftyp" box near the start.
    assert b"ftyp" in video_path.read_bytes()[:32]


def test_get_playback_returns_hls_kind_url() -> None:
    playback = FakeStreamProvider().get_playback(STREAM)

    assert playback.kind == "hls"
    assert str(playback.url).endswith(DEMO_VIDEO_PATH)
    assert playback.is_live is True


def test_get_playback_offline_flag_marks_not_live() -> None:
    playback = FakeStreamProvider(offline=True).get_playback(STREAM)

    assert playback.is_live is False


def test_get_playback_raises_on_fail_flag() -> None:
    with pytest.raises(StreamProviderError):
        FakeStreamProvider(fail=True).get_playback(STREAM)


def test_check_health_reflects_offline_flag() -> None:
    assert FakeStreamProvider().check_health(STREAM).status == "online"
    assert FakeStreamProvider(offline=True).check_health(STREAM).status == "offline"


def test_grab_snapshot_returns_poster_bytes() -> None:
    snapshot = FakeStreamProvider().grab_snapshot(STREAM)

    poster_path = Path(settings.BASE_DIR) / "static" / DEMO_POSTER_PATH
    assert snapshot == poster_path.read_bytes()


def test_grab_snapshot_returns_none_when_offline() -> None:
    assert FakeStreamProvider(offline=True).grab_snapshot(STREAM) is None


def test_grab_snapshot_raises_on_fail_flag() -> None:
    with pytest.raises(StreamProviderError):
        FakeStreamProvider(fail=True).grab_snapshot(STREAM)
