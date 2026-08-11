"""Catalog tasks. Names are explicit so the beat schedule can reach them."""

import logging

from celery import shared_task
from django.apps import apps
from django.db.models import F

from apps.catalog.contracts import RegenerateAllPayload, RenditionsPayload
from apps.catalog.services import images, views_counter
from apps.core.contracts import EmptyPayload

logger = logging.getLogger(__name__)


@shared_task(name="catalog.generate_renditions")
def generate_renditions(payload: dict) -> str:
    """Build the presets of one photo (section 8.2).

    Idempotent through `renditions_version`: the same file and the same
    presets give the same version, and a repeat run exits without work.
    """
    from apps.catalog.models import WorkImage

    data = RenditionsPayload.model_validate(payload)

    work_image = WorkImage.objects.filter(pk=data.work_image_id).first()
    if work_image is None:
        logger.info("catalog.generate_renditions: photo %s is gone", data.work_image_id)
        return "missing"

    try:
        created = images.generate_renditions(work_image, force=data.force)
    except images.UnreadableImage:
        # A broken upload is not transient: log it and leave the photo without
        # renditions. The page shows a skeleton, the worker keeps running.
        logger.exception("catalog.generate_renditions: photo %s is unreadable", work_image.pk)
        return "unreadable"

    return "generated" if created else "unchanged"


@shared_task(name="catalog.regenerate_all_renditions")
def regenerate_all_renditions(payload: dict) -> int:
    """Fan out `generate_renditions`, used after the watermark changes (8.4)."""
    from apps.catalog.models import WorkImage

    data = RegenerateAllPayload.model_validate(payload)

    queryset = WorkImage.objects.all()
    if data.work_id is not None:
        queryset = queryset.filter(work_id=data.work_id)

    identifiers = list(queryset.values_list("pk", flat=True))
    for work_image_id in identifiers:
        generate_renditions.apply_async(
            kwargs={"payload": {"work_image_id": work_image_id, "force": data.force}}
        )
    return len(identifiers)


@shared_task(name="catalog.flush_view_counters")
def flush_view_counters(payload: dict) -> int:
    """Fold the Redis counters into the database (section 8.3).

    Idempotent by construction: the counters are taken with GETDEL, so a second
    run finds an empty Redis and adds nothing.
    """
    EmptyPayload.model_validate(payload)

    collected = views_counter.collect()
    applied = 0
    for kind, label in (("work", "catalog.Work"), ("post", "blog.Post")):
        counts = collected.get(kind) or {}
        if not counts:
            continue
        try:
            model = apps.get_model(label)
        except LookupError:
            # The blog lands in stage 3; until then its counters are dropped.
            logger.info("catalog.flush_view_counters: %s does not exist yet", label)
            continue
        for identifier, amount in counts.items():
            applied += model.objects.filter(pk=identifier).update(
                views_count=F("views_count") + amount
            )
    return applied
