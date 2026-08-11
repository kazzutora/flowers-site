"""Work photos: validation, the sanitised original, and the renditions.

Section 14.1. Originals live in the private storage and are never served;
everything the browser sees is a watermarked rendition whose file name carries
the version, so an `immutable` cache header stays safe (section 4.6).
"""

import hashlib
import io
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pillow_avif  # noqa: F401  importing registers the AVIF plugin
import pillow_heif
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from apps.catalog.models import WorkImage

# HEIC is what an iPhone produces by default.
pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)

# Bumped whenever a preset or the watermarking changes: it is half of
# `renditions_version`, so bumping it regenerates everything (section 8.2).
PRESETS_VERSION = "v1"

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MIN_SIDE = 800
ALLOWED_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP", "HEIF", "MPO"})

# Pillow format name and file extension per stored format.
_ENCODERS: dict[str, tuple[str, str, dict[str, Any]]] = {
    "avif": ("AVIF", "avif", {"quality": 55}),
    "webp": ("WEBP", "webp", {"quality": 82, "method": 6}),
    "jpeg": ("JPEG", "jpg", {"quality": 85, "optimize": True, "progressive": True}),
}

_ORIGINAL_SAVE_OPTIONS: dict[str, dict[str, Any]] = {
    "JPEG": {"quality": 90, "optimize": True, "progressive": True},
    "PNG": {"optimize": True},
    "WEBP": {"quality": 90, "method": 6},
    "HEIF": {"quality": 90},
    "MPO": {"quality": 90},
}

_EXTENSIONS: dict[str, str] = {
    "JPEG": "jpg",
    "MPO": "jpg",
    "PNG": "png",
    "WEBP": "webp",
    "HEIF": "heic",
}


@dataclass(frozen=True)
class Preset:
    """One derived size. `crop` wins over `long_side` when both are set."""

    name: str
    long_side: int | None = None
    crop: tuple[int, int] | None = None
    formats: tuple[str, ...] = field(default=("avif", "webp"))


PRESETS: tuple[Preset, ...] = (
    Preset("thumb", long_side=400),
    Preset("card", long_side=800),
    Preset("large", long_side=1600),
    # jpeg as well: several messengers decode neither avif nor webp in a
    # link preview.
    Preset("og", crop=(1200, 630), formats=("avif", "webp", "jpeg")),
)


class UnreadableImage(Exception):
    """The stored file is not an image we can decode. Retrying cannot help."""


# --- upload validation --------------------------------------------------------


def validate_work_photo(file: Any) -> None:
    """Field validator: format, weight and the shortest side (section 14.1)."""
    size = getattr(file, "size", 0) or 0
    if size > MAX_UPLOAD_BYTES:
        raise ValidationError(
            _("The photo is heavier than %(limit)d MB."),
            params={"limit": MAX_UPLOAD_BYTES // (1024 * 1024)},
        )

    position = file.tell() if hasattr(file, "tell") else None
    try:
        with Image.open(file) as image:
            image_format = (image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(_("This file is not an image we can read.")) from exc
    finally:
        if position is not None:
            file.seek(position)

    if image_format not in ALLOWED_FORMATS:
        raise ValidationError(
            _("Format %(format)s is not supported. Use JPEG, PNG, WebP or HEIC."),
            params={"format": image_format or "?"},
        )
    if min(width, height) < MIN_SIDE:
        raise ValidationError(
            _("The photo is too small: the shortest side must be at least %(side)d px."),
            params={"side": MIN_SIDE},
        )


# --- the original -------------------------------------------------------------


def process_original(file: Any, name: str) -> "ContentFile[bytes]":
    """Apply the EXIF orientation and drop every piece of metadata.

    GPS coordinates travel inside a phone photo and would publish the owner's
    home address, so nothing but pixels is kept.
    """
    with Image.open(file) as source:
        image_format = (source.format or "JPEG").upper()
        rotated = ImageOps.exif_transpose(source) or source
        # A brand new canvas carries no `info`: no EXIF, no ICC profile, no GPS.
        stripped = Image.new(rotated.mode, rotated.size)
        stripped.paste(rotated)

    if image_format in {"JPEG", "MPO"} and stripped.mode not in {"RGB", "L"}:
        stripped = stripped.convert("RGB")

    buffer = io.BytesIO()
    stripped.save(buffer, format=image_format, **_ORIGINAL_SAVE_OPTIONS.get(image_format, {}))
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0] or "photo"
    extension = _EXTENSIONS.get(image_format, "jpg")
    return ContentFile(buffer.getvalue(), name=f"{stem}.{extension}")


def file_digest(stored: FieldFile) -> str:
    """sha256 of the stored bytes, shortened. Half of `renditions_version`.

    Reads through the storage rather than through the field file: closing the
    field file would leave the caller with a handle it can no longer seek.
    """
    digest = hashlib.sha256()
    with stored.storage.open(str(stored.name), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 256), b""):
            digest.update(chunk)
    return digest.hexdigest()[:32]


def renditions_version(stored: FieldFile) -> str:
    return f"{file_digest(stored)}:{PRESETS_VERSION}"


def version_slug(version: str) -> str:
    """The version as it appears in a file name; a colon has no place there."""
    return version.replace(":", "-")


# --- watermark ----------------------------------------------------------------


def _watermark_layer(canvas: Image.Image, settings: Any) -> Image.Image | None:
    """The watermark scaled and placed for this canvas, or None when unset."""
    if not settings.watermark_image:
        return None

    try:
        with Image.open(settings.watermark_image) as source:
            mark = source.convert("RGBA")
    except (UnidentifiedImageError, OSError, ValueError):
        logger.warning("watermark image cannot be read, renditions stay clean", exc_info=True)
        return None

    target_width = max(1, int(canvas.width * float(settings.watermark_scale or 0.18)))
    ratio = target_width / mark.width
    mark = mark.resize((target_width, max(1, int(mark.height * ratio))), Image.Resampling.LANCZOS)

    opacity = min(max(float(settings.watermark_opacity or 0.0), 0.0), 1.0)
    if opacity < 1.0:
        alpha = mark.getchannel("A").point(lambda value: int(value * opacity))
        mark.putalpha(alpha)

    margin = max(8, canvas.width // 40)
    if settings.watermark_position == "bottom_left":
        position = (margin, canvas.height - mark.height - margin)
    elif settings.watermark_position == "center":
        position = ((canvas.width - mark.width) // 2, (canvas.height - mark.height) // 2)
    else:
        position = (canvas.width - mark.width - margin, canvas.height - mark.height - margin)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(mark, position, mark)
    return layer


def _watermarked(canvas: Image.Image, settings: Any) -> Image.Image:
    layer = _watermark_layer(canvas, settings)
    if layer is None:
        return canvas.convert("RGB")
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


# --- renditions ---------------------------------------------------------------


def _sized(base: Image.Image, preset: Preset) -> Image.Image:
    if preset.crop is not None:
        return ImageOps.fit(base, preset.crop, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    copy = base.copy()
    if preset.long_side is not None:
        # thumbnail never enlarges: a small original stays small.
        copy.thumbnail((preset.long_side, preset.long_side), Image.Resampling.LANCZOS)
    return copy


def _encode(canvas: Image.Image, image_format: str) -> tuple[bytes, int, int]:
    pillow_format, _extension, options = _ENCODERS[image_format]
    buffer = io.BytesIO()
    canvas.save(buffer, format=pillow_format, **options)
    return buffer.getvalue(), canvas.width, canvas.height


def discard_renditions(work_image: "WorkImage") -> None:
    """Drop the derived rows and their files. The originals stay untouched."""
    for rendition in list(work_image.renditions.all()):
        rendition.file.delete(save=False)
        rendition.delete()


def generate_renditions(work_image: "WorkImage", force: bool = False) -> bool:
    """Build every preset. Returns False when the work was already done.

    Idempotent through `renditions_version`: the same bytes and the same
    presets produce the same version, and a second run does nothing.
    """
    from apps.catalog.models import WorkImage, WorkImageRendition
    from apps.core.models import SiteSettings

    if not work_image.image:
        return False

    version = renditions_version(work_image.image)
    if not force and work_image.renditions_ready and work_image.renditions_version == version:
        return False

    stored = work_image.image
    try:
        with (
            stored.storage.open(str(stored.name), "rb") as handle,
            Image.open(handle) as source,
        ):
            base = ImageOps.exif_transpose(source) or source
            base.load()
            base = base.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise UnreadableImage(str(exc)) from exc

    settings = SiteSettings.load()
    discard_renditions(work_image)

    slug = version_slug(version)
    for preset in PRESETS:
        canvas = _watermarked(_sized(base, preset), settings)
        for image_format in preset.formats:
            data, width, height = _encode(canvas, image_format)
            extension = _ENCODERS[image_format][1]
            WorkImageRendition.objects.create(
                source=work_image,
                preset=preset.name,
                image_format=image_format,
                file=ContentFile(data, name=f"{work_image.pk}_{preset.name}_{slug}.{extension}"),
                width=width,
                height=height,
                bytes=len(data),
            )

    # `update` and not `save`: saving would enqueue the task again.
    WorkImage.objects.filter(pk=work_image.pk).update(
        renditions_ready=True, renditions_version=version
    )
    work_image.renditions_ready = True
    work_image.renditions_version = version
    return True
