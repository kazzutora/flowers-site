"""Works close to the one on screen (section 10, "work page").

Occasions first, tags second, the current work never among them.
"""

from typing import TYPE_CHECKING, Any

from django.db.models import Count, Q, QuerySet

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from apps.catalog.models import Work

LIMIT = 8


def similar_works(work: "Work", limit: int = LIMIT) -> "QuerySet[Any]":
    from apps.catalog.models import Work as WorkModel

    occasion_ids = list(work.occasions.values_list("pk", flat=True))
    tag_ids = list(work.tags.values_list("pk", flat=True))
    if not occasion_ids and not tag_ids:
        return WorkModel.published.none()

    return (
        WorkModel.published.exclude(pk=work.pk)
        .annotate(
            shared_occasions=Count(
                "occasions", filter=Q(occasions__in=occasion_ids), distinct=True
            ),
            shared_tags=Count("tags", filter=Q(tags__in=tag_ids), distinct=True),
        )
        .filter(Q(shared_occasions__gt=0) | Q(shared_tags__gt=0))
        # `-id` again: without it equal scores come back in whatever order the
        # planner feels like.
        .order_by("-shared_occasions", "-shared_tags", "-id")
        .prefetch_related("images__renditions")[:limit]
    )
