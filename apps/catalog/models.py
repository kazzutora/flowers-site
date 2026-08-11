"""Catalog schema, sections 4.1 to 4.6 of tech.md.

The field set is frozen: nothing here exists that the contract does not list.
"""

from typing import Any

from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.catalog.services.images import process_original, validate_work_photo
from apps.core.models import TranslatedMixin
from apps.core.services.images import compress_field
from config.storages import private_storage, public_storage

# Query parameter names the gallery owns (section 4.3). A tag slug may not
# collide with them, otherwise the slug alone no longer identifies a group.
RESERVED_QUERY_NAMES: frozenset[str] = frozenset({"sort", "page", "q", "a"})

ARTICLE_SEQUENCE = "work_article_seq"
SLUG_TITLE_LIMIT = 180

# Ukrainian national transliteration. Five letters take a different form at the
# start of a word, which is why the table is split in two.
_TRANSLIT: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia",
    # Russian letters a bilingual keyboard produces by accident.
    "ъ": "", "ы": "y", "э": "e", "ё": "e",
}  # fmt: skip
_TRANSLIT_WORD_START: dict[str, str] = {"є": "ye", "ї": "yi", "й": "y", "ю": "yu", "я": "ya"}
_APOSTROPHES = "'’ʼʻ`"


def translit(value: str) -> str:
    """Cyrillic text as an ASCII slug fragment. Anything else is dropped."""
    letters: list[str] = []
    word_start = True
    for char in value:
        lower = char.lower()
        if lower in _APOSTROPHES:
            # An apostrophe separates letters but does not start a new word.
            continue
        if lower in _TRANSLIT:
            table = _TRANSLIT_WORD_START if word_start else _TRANSLIT
            letters.append(table.get(lower, _TRANSLIT[lower]))
            word_start = False
        elif lower.isascii() and lower.isalnum():
            letters.append(lower)
            word_start = False
        else:
            letters.append(" ")
            word_start = True
    # slugify also guarantees the result is ASCII: emoji and CJK do not survive.
    return slugify("".join(letters))


def build_work_slug(article: int, title: str) -> str:
    """`<article>-<translit(title)>`, or the bare article when there is no title.

    Unique by construction: the article is unique and never reused.
    """
    tail = translit(title)[:SLUG_TITLE_LIMIT].strip("-")
    return f"{article}-{tail}" if tail else str(article)


def next_article() -> int:
    """Next value of the sequence created by the initial migration.

    A rolled back transaction does not give the number back. That is how
    sequences work and here it is the wanted behaviour: an article is never
    reused (section 5).
    """
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT nextval('{ARTICLE_SEQUENCE}')")
        row = cursor.fetchone()
    return int(row[0])


class Occasion(TranslatedMixin, models.Model):
    """A catalog section: it lives in the path, not in the query (section 1)."""

    slug = models.SlugField(_("slug"), max_length=60, unique=True)
    name_uk = models.CharField(_("name, uk"), max_length=100)
    name_ru = models.CharField(_("name, ru"), max_length=100, blank=True)
    description_uk = models.TextField(_("description, uk"), blank=True)
    description_ru = models.TextField(_("description, ru"), blank=True)
    cover = models.ImageField(
        _("cover"), upload_to="occasions/", storage=public_storage, blank=True
    )
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_active = models.BooleanField(_("active"), default=True)
    show_on_home = models.BooleanField(_("show on the home page"), default=True)
    seo_title_uk = models.CharField(_("SEO title, uk"), max_length=200, blank=True)
    seo_title_ru = models.CharField(_("SEO title, ru"), max_length=200, blank=True)
    seo_description_uk = models.CharField(_("SEO description, uk"), max_length=300, blank=True)
    seo_description_ru = models.CharField(_("SEO description, ru"), max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["is_active", "order"], name="occasion_active_order_idx")]
        verbose_name = _("occasion")
        verbose_name_plural = _("occasions")

    def __str__(self) -> str:
        return self.name_uk

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Section 14.2: tiles get no rendition pipeline, they are squeezed once.
        compress_field(self, "cover")
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("gallery_occasion", kwargs={"occasion_slug": self.slug})


class TagGroup(TranslatedMixin, models.Model):
    """A block of the filter panel. Its slug is the query parameter name."""

    class FilterKind(models.TextChoices):
        CHECKBOX = "checkbox", _("Checkboxes")
        COLOR_SWATCH = "color_swatch", _("Colour swatches")

    slug = models.SlugField(_("slug"), max_length=40, unique=True)
    name_uk = models.CharField(_("name, uk"), max_length=100)
    name_ru = models.CharField(_("name, ru"), max_length=100, blank=True)
    filter_kind = models.CharField(
        _("filter kind"), max_length=20, choices=FilterKind.choices, default=FilterKind.CHECKBOX
    )
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("tag group")
        verbose_name_plural = _("tag groups")

    def __str__(self) -> str:
        return self.name_uk


class Tag(TranslatedMixin, models.Model):
    """A filter value. Its slug is the query parameter value."""

    group = models.ForeignKey(
        TagGroup,
        verbose_name=_("group"),
        related_name="tags",
        on_delete=models.PROTECT,
    )
    # Globally unique, not unique per group: the slug alone has to identify the
    # group it belongs to.
    slug = models.SlugField(_("slug"), max_length=60, unique=True)
    name_uk = models.CharField(_("name, uk"), max_length=100)
    name_ru = models.CharField(_("name, ru"), max_length=100, blank=True)
    color_hex = models.CharField(_("colour"), max_length=7, blank=True)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def __str__(self) -> str:
        return self.name_uk

    def clean(self) -> None:
        super().clean()
        errors: dict[str, Any] = {}

        if self.group_id:
            if self.group.filter_kind == TagGroup.FilterKind.COLOR_SWATCH:
                if not self.color_hex:
                    errors["color_hex"] = _("A colour swatch tag needs a colour.")
            elif self.color_hex:
                errors["color_hex"] = _("Only colour swatch tags carry a colour.")

        if self.slug:
            if self.slug in RESERVED_QUERY_NAMES:
                errors["slug"] = _("This slug is a reserved query parameter name.")
            elif TagGroup.objects.filter(slug=self.slug).exists():
                errors["slug"] = _("A tag group already answers to this slug.")

        if errors:
            raise ValidationError(errors)


class PublishedWorkManager(models.Manager["Work"]):
    def get_queryset(self) -> models.QuerySet["Work"]:
        return (
            super()
            .get_queryset()
            .filter(status=Work.Status.PUBLISHED, published_at__lte=timezone.now())
        )


class Work(TranslatedMixin, models.Model):
    """One piece of work with its photos. Nothing is ever deleted, only archived."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    article = models.PositiveIntegerField(_("article"), unique=True, editable=False)
    slug = models.SlugField(_("slug"), max_length=200, unique=True, editable=False)
    title_uk = models.CharField(_("title, uk"), max_length=200, blank=True)
    title_ru = models.CharField(_("title, ru"), max_length=200, blank=True)
    description_uk = models.TextField(_("description, uk"), blank=True)
    description_ru = models.TextField(_("description, ru"), blank=True)
    composition_uk = models.CharField(_("composition, uk"), max_length=300, blank=True)
    composition_ru = models.CharField(_("composition, ru"), max_length=300, blank=True)
    size_text_uk = models.CharField(_("size, uk"), max_length=100, blank=True)
    size_text_ru = models.CharField(_("size, ru"), max_length=100, blank=True)
    occasions = models.ManyToManyField(
        Occasion, verbose_name=_("occasions"), related_name="works", blank=True
    )
    tags = models.ManyToManyField(Tag, verbose_name=_("tags"), related_name="works", blank=True)
    price_from = models.DecimalField(
        _("price from"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_to = models.DecimalField(
        _("price to"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(_("currency"), max_length=3, default="UAH")
    price_visible = models.BooleanField(_("show the price"), default=False)
    price_note_uk = models.CharField(_("price note, uk"), max_length=200, blank=True)
    price_note_ru = models.CharField(_("price note, ru"), max_length=200, blank=True)
    # Purchase cost. Admin only: it is never put into a template context.
    cost = models.DecimalField(_("cost"), max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    is_pinned = models.BooleanField(_("pinned"), default=False)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    views_count = models.PositiveIntegerField(_("views"), default=0)
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)
    seo_title_uk = models.CharField(_("SEO title, uk"), max_length=200, blank=True)
    seo_title_ru = models.CharField(_("SEO title, ru"), max_length=200, blank=True)
    seo_description_uk = models.CharField(_("SEO description, uk"), max_length=300, blank=True)
    seo_description_ru = models.CharField(_("SEO description, ru"), max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedWorkManager()

    class Meta:
        # nulls_last keeps drafts and unscheduled works from floating to the top.
        ordering = ["-is_pinned", "order", F("published_at").desc(nulls_last=True), "-id"]
        indexes = [
            models.Index(fields=["status", "published_at"], name="work_status_published_idx"),
            models.Index(fields=["status", "is_pinned", "order"], name="work_status_pinned_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price_to__isnull=True)
                | Q(price_from__isnull=True)
                | Q(price_to__gte=F("price_from")),
                name="price_range_valid",
            )
        ]
        verbose_name = _("work")
        verbose_name_plural = _("works")

    def __str__(self) -> str:
        return f"№{self.article} {self.title_uk}".strip()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding and not self.article:
            self.article = next_article()
        # Computed once. Editing the title later must not break existing links.
        if not self.slug:
            self.slug = build_work_slug(self.article, self.title_uk)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("work_detail", kwargs={"slug": self.slug})

    @property
    def main_image(self) -> "WorkImage | None":
        """The photo flagged is_main, or the first one. Uses the prefetch cache."""
        images = list(self.images.all())
        for image in images:
            if image.is_main:
                return image
        return images[0] if images else None


class WorkImage(TranslatedMixin, models.Model):
    """An original photo. It lives in the private storage and has no public URL."""

    work = models.ForeignKey(
        Work, verbose_name=_("work"), related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(
        _("photo"),
        upload_to="works/%Y/%m/",
        storage=private_storage,
        width_field="width",
        height_field="height",
        validators=[validate_work_photo],
    )
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    alt_uk = models.CharField(_("alt text, uk"), max_length=200, blank=True)
    alt_ru = models.CharField(_("alt text, ru"), max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_main = models.BooleanField(_("main photo"), default=False)
    renditions_ready = models.BooleanField(_("renditions ready"), default=False, editable=False)
    renditions_version = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["work"], condition=Q(is_main=True), name="one_main_image_per_work"
            )
        ]
        verbose_name = _("work photo")
        verbose_name_plural = _("work photos")

    def __str__(self) -> str:
        return f"{self.work_id}/{self.pk}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        creating = self._state.adding
        siblings = WorkImage.objects.filter(work_id=self.work_id).exclude(pk=self.pk)

        # `_committed` is False only while the field holds a fresh upload, which
        # is exactly when the original has to be stripped of its metadata.
        if self.image and not getattr(self.image, "_committed", True):
            self.image = process_original(self.image.file, str(self.image.name))

        if creating and not self.order:
            # Photos added one after another line up 0, 1, 2; dragging in the
            # admin overwrites this later.
            self.order = siblings.count()
        if not self.is_main and not siblings.filter(is_main=True).exists():
            # The first photo of a work is its main photo.
            self.is_main = True

        with transaction.atomic():
            if self.is_main:
                # The partial unique index is immediate, so the old main has to
                # step aside first.
                siblings.filter(is_main=True).update(is_main=False)
            super().save(*args, **kwargs)

    @property
    def alt_text(self) -> str:
        """Owner written alt, or one built from the work title and its occasion."""
        written = self.tr("alt")
        if written:
            return written
        title = self.work.tr("title")
        if title:
            return title
        occasion = self.work.occasions.first()
        if occasion is not None:
            return str(occasion.tr("name"))
        return ""


@receiver(post_save, sender=WorkImage)
def enqueue_renditions(sender: type[WorkImage], instance: WorkImage, **kwargs: Any) -> None:
    """Queue the derived images once the row is really committed (section 14.1).

    Imported inside the function: `tasks` imports the models back.
    """
    from apps.catalog.tasks import generate_renditions

    work_image_id = instance.pk
    transaction.on_commit(
        lambda: generate_renditions.apply_async(
            kwargs={"payload": {"work_image_id": work_image_id}}, queue="media"
        )
    )


@receiver(post_delete, sender=WorkImage)
def promote_next_main_image(sender: type[WorkImage], instance: WorkImage, **kwargs: Any) -> None:
    """Deleting the main photo makes the first remaining one main."""
    if not instance.is_main:
        return
    replacement = WorkImage.objects.filter(work_id=instance.work_id).order_by("order", "id").first()
    if replacement is not None:
        WorkImage.objects.filter(pk=replacement.pk).update(is_main=True)


class WorkImageRendition(models.Model):
    """A derived image. Watermarked, public, and named after its version."""

    class Preset(models.TextChoices):
        THUMB = "thumb", _("Thumbnail")
        CARD = "card", _("Card")
        LARGE = "large", _("Large")
        OG = "og", _("Link preview")

    class ImageFormat(models.TextChoices):
        AVIF = "avif", "AVIF"
        WEBP = "webp", "WebP"
        JPEG = "jpeg", "JPEG"

    source = models.ForeignKey(
        WorkImage, verbose_name=_("source"), related_name="renditions", on_delete=models.CASCADE
    )
    preset = models.CharField(_("preset"), max_length=10, choices=Preset.choices)
    image_format = models.CharField(_("format"), max_length=10, choices=ImageFormat.choices)
    # No width_field/height_field: the generator already knows the size and
    # must not make the database reopen a file it just wrote.
    file = models.ImageField(_("file"), upload_to="renditions/%Y/%m/", storage=public_storage)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    bytes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["preset", "image_format"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "preset", "image_format"], name="one_rendition_per_variant"
            )
        ]
        verbose_name = _("rendition")
        verbose_name_plural = _("renditions")

    def __str__(self) -> str:
        return f"{self.source_id} {self.preset} {self.image_format}"
