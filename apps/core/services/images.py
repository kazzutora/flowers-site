"""One-off compression for every image that is not a work photo.

Section 14.2: covers, occasion tiles, the hero and review photos get no
rendition pipeline. They are compressed once on upload and rendered by
`ui/image_simple.html`.
"""

import io
import logging
from typing import Any

import pillow_heif
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)

LONG_SIDE = 1600
QUALITY = 82


def compress_simple_image(file: Any, name: str) -> "ContentFile[bytes] | None":
    """Long side down to 1600 px, converted to webp, metadata dropped.

    Returns None when the file cannot be decoded: a broken upload must not
    take the save down with it.
    """
    try:
        with Image.open(file) as source:
            rotated = ImageOps.exif_transpose(source) or source
            rotated.load()
            has_alpha = rotated.mode in {"RGBA", "LA", "P"}
            canvas = rotated.convert("RGBA" if has_alpha else "RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        logger.warning("image %s cannot be read and was stored as is", name, exc_info=True)
        return None

    canvas.thumbnail((LONG_SIDE, LONG_SIDE), Image.Resampling.LANCZOS)
    # A new canvas carries no EXIF, so nothing about the camera or the place
    # survives the upload.
    stripped = Image.new(canvas.mode, canvas.size)
    stripped.paste(canvas)

    buffer = io.BytesIO()
    stripped.save(buffer, format="WEBP", quality=QUALITY, method=6)
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0] or "image"
    return ContentFile(buffer.getvalue(), name=f"{stem}.webp")


def compress_field(instance: Any, field_name: str) -> None:
    """Compress an image field in place when it holds a fresh upload."""
    stored = getattr(instance, field_name, None)
    if not stored or getattr(stored, "_committed", True):
        return
    compressed = compress_simple_image(stored.file, stored.name)
    if compressed is not None:
        setattr(instance, field_name, compressed)
