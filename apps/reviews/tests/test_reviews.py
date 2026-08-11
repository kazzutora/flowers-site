"""Sections 4.10, 8.6, 15 and 16: reviews, moderation and the rating."""

import time
from typing import Any

import pytest
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from pydantic import ValidationError as PayloadError

from apps.leads.services import antispam, ratelimit
from apps.reviews.models import Review
from apps.reviews.tasks import build_message, notify_new_review
from clients.factory import fake_telegram_client
from tests.factories import ReviewFactory, SiteSettingsFactory, photo_bytes

pytestmark = pytest.mark.django_db

REVIEW_URL = "/hx/review/"


@pytest.fixture(autouse=True)
def site() -> Any:
    return SiteSettingsFactory.create()


@pytest.fixture(autouse=True)
def telegram() -> Any:
    fake_telegram_client.reset()
    yield fake_telegram_client
    fake_telegram_client.reset()


@pytest.fixture(autouse=True)
def clean_limits() -> Any:
    try:
        client = ratelimit.get_client()
        client.ping()
    except Exception:  # pragma: no cover - only on a machine without Redis
        pytest.skip("redis is not reachable")

    def clear() -> None:
        for pattern in ("review:*", "lead:*"):
            for key in client.scan_iter(match=pattern, count=500):
                client.delete(key)

    clear()
    yield client
    clear()


def _payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "ts": signing.dumps(time.time() - 30, salt=antispam.TIMESTAMP_SALT),
        "author_name": "Олена",
        "text_uk": "Букет був свіжий, зібрали за годину.",
        "rating": "5",
        "contact_phone": "",
        "consent": "on",
        "website": "",
    }
    data.update(overrides)
    return data


# --- the model ----------------------------------------------------------------


def test_a_rating_outside_one_to_five_is_refused_by_the_database() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        ReviewFactory.create(rating=6)


def test_a_review_without_a_rating_is_fine() -> None:
    assert ReviewFactory.create(rating=None).pk is not None


def test_a_review_needs_text_in_at_least_one_language() -> None:
    review = Review(author_name="Олена", text_uk="", text_ru="")

    with pytest.raises(ValidationError) as error:
        review.full_clean()

    assert "text_uk" in error.value.error_dict


def test_a_review_from_the_site_needs_consent() -> None:
    review = Review(author_name="Олена", text_uk="Дякую", source=Review.Source.SITE, consent=False)

    with pytest.raises(ValidationError) as error:
        review.full_clean()

    assert "consent" in error.value.error_dict


def test_publishing_stamps_published_at_once() -> None:
    review = ReviewFactory.create(status=Review.Status.PENDING)
    assert review.published_at is None

    review.status = Review.Status.PUBLISHED
    review.save()
    stamped = review.published_at

    review.author_name = "Інша Олена"
    review.save()

    assert review.published_at == stamped


def test_a_photo_is_squeezed_once_and_gets_no_renditions() -> None:
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    from apps.catalog.models import WorkImageRendition

    review = ReviewFactory.create(
        photo=SimpleUploadedFile("photo.jpg", photo_bytes(3000, 2000), "image/jpeg")
    )

    assert str(review.photo.name).endswith(".webp")
    with Image.open(review.photo) as stored:
        assert stored.format == "WEBP"
        assert max(stored.size) == 1600
    assert WorkImageRendition.objects.count() == 0


# --- the public page ----------------------------------------------------------


def test_the_list_shows_published_reviews(client: Client) -> None:
    ReviewFactory.create(author_name="Олена", text_uk="Все чудово")

    body = client.get("/vidhuky/").content.decode()

    assert "Олена" in body
    assert "Все чудово" in body


def test_pending_and_rejected_reviews_stay_out_of_the_html(client: Client) -> None:
    ReviewFactory.create(author_name="Чекає", status=Review.Status.PENDING)
    ReviewFactory.create(author_name="Відхилено", status=Review.Status.REJECTED)
    ReviewFactory.create(author_name="Опубліковано")

    for url in ("/vidhuky/", "/"):
        body = client.get(url).content.decode()
        assert "Чекає" not in body, url
        assert "Відхилено" not in body, url


def test_the_contact_phone_never_reaches_a_page(client: Client) -> None:
    ReviewFactory.create(author_name="Олена", contact_phone="+380509998877", is_featured=True)

    for url in ("/vidhuky/", "/"):
        body = client.get(url).content.decode()
        assert "509998877" not in body, url


def test_an_empty_list_says_so(client: Client) -> None:
    body = client.get("/vidhuky/").content.decode()

    assert "Відгуків поки немає" in body or "No reviews yet" in body


def test_the_home_page_shows_the_featured_ones(client: Client) -> None:
    ReviewFactory.create(author_name="На головній", is_featured=True)
    ReviewFactory.create(author_name="Не на головній", is_featured=False)

    body = client.get("/").content.decode()

    assert "На головній" in body
    assert "Не на головній" not in body


# --- leaving a review ---------------------------------------------------------


def test_a_review_from_the_site_waits_for_moderation(client: Client) -> None:
    response = client.post(REVIEW_URL, _payload())

    review = Review.objects.get()
    assert response.status_code == 302
    assert review.status == Review.Status.PENDING
    assert review.source == Review.Source.SITE
    assert review.published_at is None
    assert "Олена" not in client.get("/vidhuky/").content.decode()


def test_htmx_gets_a_redirect_header(client: Client) -> None:
    response = client.post(REVIEW_URL, _payload(), headers={"HX-Request": "true"})

    assert response.headers["HX-Redirect"] == "/dyakuyemo/"


def test_a_review_from_the_admin_is_published_at_once(admin_client: Client) -> None:
    response = admin_client.post(
        "/admin/reviews/review/add/",
        {
            "author_name": "Олена",
            "text_uk": "Дякую за букет",
            "text_ru": "",
            "rating": "5",
            "status": Review.Status.PUBLISHED,
            "source": Review.Source.ADMIN,
            "consent": "on",
            "published_at_0": "",
            "published_at_1": "",
            "contact_phone": "",
        },
    )

    assert response.status_code == 302
    review = Review.objects.get()
    assert review.status == Review.Status.PUBLISHED
    assert review.published_at is not None


def test_moderation_publishes_in_bulk(admin_client: Client) -> None:
    waiting = ReviewFactory.create(status=Review.Status.PENDING)

    admin_client.post(
        "/admin/reviews/review/",
        {"action": "publish", "_selected_action": [str(waiting.pk)], "index": "0"},
        follow=True,
    )
    waiting.refresh_from_db()

    assert waiting.status == Review.Status.PUBLISHED
    assert waiting.published_at is not None


def test_without_consent_the_form_comes_back(client: Client) -> None:
    response = client.post(REVIEW_URL, _payload(consent=""))

    assert response.status_code == 200
    assert Review.objects.count() == 0


def test_a_rating_is_optional(client: Client) -> None:
    client.post(REVIEW_URL, _payload(rating=""))

    assert Review.objects.get().rating is None


# --- antispam -----------------------------------------------------------------


def test_the_trap_answers_like_a_success_and_writes_nothing(client: Client) -> None:
    response = client.post(REVIEW_URL, _payload(website="https://buy-cheap.example"))

    assert response.status_code == 302
    assert Review.objects.count() == 0


def test_a_review_sent_too_fast_is_dropped_in_silence(client: Client) -> None:
    response = client.post(REVIEW_URL, _payload(ts=antispam.timestamp_token()))

    assert response.status_code == 302
    assert Review.objects.count() == 0


def test_the_review_limit_and_the_enquiry_limit_are_counted_apart(
    client: Client, clean_limits: Any
) -> None:
    """Section 15 gives each form its own keys."""
    for _index in range(3):
        client.post(REVIEW_URL, _payload())

    assert Review.objects.filter(status=Review.Status.REJECTED).count() == 1

    lead = {
        "form": "callback",
        "ts": signing.dumps(time.time() - 30, salt=antispam.TIMESTAMP_SALT),
        "name": "Олена",
        "phone": "0501234567",
        "consent": "on",
    }
    client.post("/hx/lead/", lead)

    from apps.leads.models import Lead

    assert Lead.objects.get().status == Lead.Status.NEW, "the review must not spend this quota"


def test_an_unreachable_redis_never_blocks_a_review(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode() -> Any:
        raise ConnectionError("redis is down")

    monkeypatch.setattr(ratelimit, "get_client", explode)

    client.post(REVIEW_URL, _payload())

    assert Review.objects.get().status == Review.Status.PENDING


# --- the notification ---------------------------------------------------------


def test_the_message_carries_what_the_owner_needs() -> None:
    review = ReviewFactory.create(author_name="Олена", rating=5, contact_phone="+380509998877")

    text = build_message(review)

    assert "Олена" in text
    assert "5/5" in text
    assert "<code>+380509998877</code>" in text
    assert f"/admin/reviews/review/{review.pk}/change/" in text


def test_the_review_is_announced_once(telegram: Any) -> None:
    review = ReviewFactory.create(status=Review.Status.PENDING)

    first = notify_new_review(payload={"review_id": review.pk})
    second = notify_new_review(payload={"review_id": review.pk})

    assert (first, second) == ("sent", "already sent")
    assert len(telegram.sent) == 1
    review.refresh_from_db()
    assert review.notified_at is not None


def test_a_rejected_review_is_never_announced(telegram: Any) -> None:
    review = ReviewFactory.create(status=Review.Status.REJECTED)

    assert notify_new_review(payload={"review_id": review.pk}) == "rejected"
    assert telegram.sent == []


def test_a_server_error_keeps_the_review_and_counts_the_attempt(telegram: Any) -> None:
    from apps.core.exceptions import TransientError

    review = ReviewFactory.create(status=Review.Status.PENDING)
    telegram.fail_with(500)

    with pytest.raises(TransientError):
        notify_new_review(payload={"review_id": review.pk})

    review.refresh_from_db()
    assert review.notified_at is None
    assert review.notify_attempts == 1


def test_the_payload_is_validated() -> None:
    with pytest.raises(PayloadError):
        notify_new_review(payload={"review_id": 0})
    with pytest.raises(PayloadError):
        notify_new_review(payload={"review_id": 1, "urgent": True})


# --- the aggregate rating -----------------------------------------------------


def test_four_rated_reviews_are_not_enough_for_a_rating(client: Client) -> None:
    for _index in range(4):
        ReviewFactory.create(rating=5)

    assert "AggregateRating" not in client.get("/").content.decode()


def test_five_rated_reviews_bring_the_rating(client: Client) -> None:
    for _index in range(4):
        ReviewFactory.create(rating=5)
    ReviewFactory.create(rating=4)

    for url in ("/", "/kontakty/"):
        body = client.get(url).content.decode()
        assert '"@type": "AggregateRating"' in body, url
        assert '"reviewCount": 5' in body, url
        assert '"ratingValue": 4.8' in body, url


def test_unrated_and_unpublished_reviews_do_not_count(client: Client) -> None:
    for _index in range(4):
        ReviewFactory.create(rating=5)
    ReviewFactory.create(rating=None)
    ReviewFactory.create(rating=5, status=Review.Status.PENDING)

    assert "AggregateRating" not in client.get("/").content.decode()
