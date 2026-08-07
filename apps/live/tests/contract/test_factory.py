import pytest
from pytest_django.fixtures import Settings

from apps.live.clients.factory import get_stream_provider
from apps.live.clients.fake import FakeStreamProvider


def test_returns_fake_provider_when_configured(settings: Settings) -> None:
    settings.STREAM_PROVIDER = "fake"

    assert isinstance(get_stream_provider(), FakeStreamProvider)


def test_raises_for_unimplemented_provider(settings: Settings) -> None:
    settings.STREAM_PROVIDER = "mediamtx"

    with pytest.raises(NotImplementedError):
        get_stream_provider()
