"""Storage handles used by model fields.

Callables, not instances: Django serialises a callable storage by reference in
migrations, so the concrete backend and its paths never leak into a migration
file.
"""

from typing import Any

from django.core.files.storage import FileSystemStorage, Storage, storages


class PrivateFileSystemStorage(FileSystemStorage):
    """Local storage for originals.

    FileSystemStorage falls back to MEDIA_URL when it has no base_url, which
    would hand out public looking URLs for files nginx never serves. Asking this
    storage for a URL is a bug and says so.
    """

    def url(self, name: Any) -> str:
        raise ValueError("private storage is not served over HTTP")


def public_storage() -> Storage:
    """Served by nginx under MEDIA_URL."""
    return storages["default"]


def private_storage() -> Storage:
    """Originals of work photos. Never mapped to a URL."""
    return storages["private"]
