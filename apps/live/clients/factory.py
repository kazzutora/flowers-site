"""Factory selects an implementation by ``settings.STREAM_PROVIDER``
(tech.md §4.3, §9.1). Services and views call this, never a concrete
provider class — the page, player and states don't change when the real
camera source is picked in stage 2.
"""

from __future__ import annotations

from django.conf import settings

from apps.live.clients.base import StreamProvider
from apps.live.clients.fake import FakeStreamProvider


def get_stream_provider() -> StreamProvider:
    provider = settings.STREAM_PROVIDER
    if provider == "fake":
        return FakeStreamProvider()
    raise NotImplementedError(f"stream provider {provider!r} is not implemented yet")
