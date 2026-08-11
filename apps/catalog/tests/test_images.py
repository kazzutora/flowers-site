"""Sections 4.6, 8.2, 8.4 and 14.1: the photo pipeline."""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from pydantic import ValidationError as PayloadError

from apps.catalog.models import WorkImage, WorkImageRendition
from apps.catalog.services import images as service
from apps.catalog.tasks import generate_renditions, regenerate_all_renditions
from apps.core.models import SiteSettings
from tests.factories import WorkFactory, WorkImageFactory, photo_bytes, uploaded_photo

pytestmark = pytest.mark.django_db


def _watermark() -> SimpleUploadedFile:
    """An opaque green square: easy to spot in a pale rendition."""
    buffer = io.BytesIO()
    Image.new("RGBA", (200, 200), (0, 128, 0, 255)).save(buffer, format="PNG")
    return SimpleUploadedFile("watermark.png", buffer.getvalue(), content_type="image/png")


@pytest.fixture
def watermarked_settings() -> SiteSettings:
    settings = SiteSettings.load()
    settings.watermark_image = _watermark()
    settings.watermark_opacity = 1.0
    settings.watermark_position = SiteSettings.WatermarkPosition.CENTER
    settings.watermark_scale = 0.5
    settings.save()
    return settings


# --- upload validation --------------------------------------------------------


def test_a_photo_smaller_than_the_minimum_is_refused() -> None:
    small = SimpleUploadedFile("small.jpg", photo_bytes(400, 500), content_type="image/jpeg")

    with pytest.raises(ValidationError):
        service.validate_work_photo(small)


def test_a_file_that_is_not_an_image_is_refused() -> None:
    with pytest.raises(ValidationError):
        service.validate_work_photo(SimpleUploadedFile("note.txt", b"not an image"))


def test_a_normal_photo_passes_validation() -> None:
    service.validate_work_photo(uploaded_photo())


def test_a_heic_photo_from_an_iphone_is_accepted_and_processed() -> None:
    heic = SimpleUploadedFile(
        "IMG_0001.HEIC",
        photo_bytes(1200, 1500, image_format="HEIF"),
        content_type="image/heic",
    )
    service.validate_work_photo(heic)

    image = WorkImage.objects.create(work=WorkFactory.create(), image=heic)

    assert image.width == 1200
    assert image.height == 1500


# --- the original -------------------------------------------------------------


def test_the_stored_original_keeps_no_metadata_and_is_already_rotated() -> None:
    source = Image.new("RGB", (1200, 1500), "#F2C9C9")
    exif = Image.Exif()
    exif[0x0112] = 6  # orientation: rotate 90 degrees clockwise
    exif[0x010F] = "SomePhone"
    buffer = io.BytesIO()
    source.save(buffer, format="JPEG", exif=exif)
    upload = SimpleUploadedFile("photo.jpg", buffer.getvalue(), content_type="image/jpeg")

    image = WorkImage.objects.create(work=WorkFactory.create(), image=upload)

    with Image.open(image.image) as stored:
        assert stored.size == (1500, 1200), "the orientation is applied, not stored"
        assert dict(stored.getexif()) == {}
    assert image.width == 1500


def test_the_original_has_no_public_url() -> None:
    image = WorkImageFactory.create()

    with pytest.raises(ValueError):
        image.image.url  # noqa: B018


# --- renditions ---------------------------------------------------------------


def test_generating_renditions_covers_every_preset_and_format() -> None:
    image = WorkImageFactory.create()

    generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()

    produced = {(item.preset, item.image_format) for item in image.renditions.all()}
    expected = {
        (preset.name, image_format) for preset in service.PRESETS for image_format in preset.formats
    }
    assert produced == expected
    assert image.renditions_ready is True


def test_running_the_task_twice_changes_nothing() -> None:
    image = WorkImageFactory.create()

    first = generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()
    version = image.renditions_version
    names = sorted(str(item.file.name) for item in image.renditions.all())
    count = image.renditions.count()

    second = generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()

    assert (first, second) == ("generated", "unchanged")
    assert image.renditions.count() == count
    assert image.renditions_version == version
    assert sorted(str(item.file.name) for item in image.renditions.all()) == names


def test_force_rebuilds_the_same_version() -> None:
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()
    version = image.renditions_version

    assert generate_renditions(payload={"work_image_id": image.pk, "force": True}) == "generated"

    image.refresh_from_db()
    assert image.renditions_version == version
    assert image.renditions.count() == sum(len(preset.formats) for preset in service.PRESETS)


def test_a_new_presets_version_rebuilds_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()
    before = image.renditions_version
    old_names = {str(item.file.name) for item in image.renditions.all()}

    monkeypatch.setattr(service, "PRESETS_VERSION", "v2")

    assert generate_renditions(payload={"work_image_id": image.pk}) == "generated"

    image.refresh_from_db()
    assert image.renditions_version != before
    assert image.renditions_version.endswith(":v2")
    assert {str(item.file.name) for item in image.renditions.all()}.isdisjoint(old_names)


def test_the_file_name_carries_the_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without it an immutable cache header would pin last year's picture."""
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})
    image.refresh_from_db()

    slug = service.version_slug(image.renditions_version)
    for rendition in image.renditions.all():
        assert slug in str(rendition.file.name)
        assert ":" not in str(rendition.file.name)


def test_the_og_preset_is_exactly_1200_by_630_in_jpeg() -> None:
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})

    og = image.renditions.get(
        preset=WorkImageRendition.Preset.OG, image_format=WorkImageRendition.ImageFormat.JPEG
    )

    assert (og.width, og.height) == (1200, 630)
    with Image.open(og.file) as rendered:
        assert rendered.size == (1200, 630)


def test_every_rendition_carries_the_watermark(watermarked_settings: SiteSettings) -> None:
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})

    for rendition in image.renditions.all():
        with Image.open(rendition.file) as rendered:
            middle = (rendered.width // 2, rendered.height // 2)
            centre = rendered.convert("RGB").getpixel(middle)
        assert isinstance(centre, tuple)
        red, green, blue = centre[:3]
        assert green > red and green > blue, f"{rendition.preset}/{rendition.image_format}"


def test_renditions_are_public_while_the_original_is_not() -> None:
    image = WorkImageFactory.create()
    generate_renditions(payload={"work_image_id": image.pk})

    for rendition in image.renditions.all():
        assert rendition.file.url.startswith("/media/")


# --- contracts and failures ---------------------------------------------------


def test_a_payload_without_a_positive_id_is_refused() -> None:
    with pytest.raises(PayloadError):
        generate_renditions(payload={"work_image_id": 0})


def test_an_unexpected_payload_key_is_refused() -> None:
    with pytest.raises(PayloadError):
        generate_renditions(payload={"work_image_id": 1, "quality": 90})


def test_a_deleted_photo_does_not_fail_the_task() -> None:
    assert generate_renditions(payload={"work_image_id": 999999}) == "missing"


def test_a_broken_file_leaves_the_photo_without_renditions() -> None:
    image = WorkImageFactory.create()
    name = str(image.image.name)
    image.image.storage.delete(name)
    image.image.storage.save(name, ContentFile(b"this is not a picture"))

    assert generate_renditions(payload={"work_image_id": image.pk}) == "unreadable"

    image.refresh_from_db()
    assert image.renditions_ready is False
    assert image.renditions.count() == 0


def test_regenerating_everything_walks_every_photo() -> None:
    work = WorkFactory.create()
    WorkImageFactory.create(work=work)
    WorkImageFactory.create(work=work)
    WorkImageFactory.create()

    assert regenerate_all_renditions(payload={"force": True}) == 3
    assert regenerate_all_renditions(payload={"work_id": work.pk}) == 2


def test_regenerate_all_refuses_an_unknown_key() -> None:
    with pytest.raises(PayloadError):
        regenerate_all_renditions(payload={"everything": True})


# --- rendering ----------------------------------------------------------------


def test_a_photo_without_renditions_renders_a_skeleton_not_the_original() -> None:
    from django.template.loader import render_to_string

    image = WorkImageFactory.create()

    html = render_to_string("ui/picture.html", {"image": image, "preset": "card"})

    assert "animate-pulse" in html
    assert "<img" not in html
