"""Storage handles used by model fields.

Callables, not instances: Django serialises a callable storage by reference in
migrations, so the concrete backend and its paths never leak into a migration
file.
"""

from django.core.files.storage import Storage, storages


def public_storage() -> Storage:
    """Served by nginx under MEDIA_URL."""
    return storages["default"]


def private_storage() -> Storage:
    """Originals of work photos. Never mapped to a URL."""
    return storages["private"]
