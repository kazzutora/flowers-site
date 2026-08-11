"""The form a visitor fills in on /vidhuky/."""

from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.reviews.models import Review

RATINGS: tuple[tuple[str, Any], ...] = (
    ("", _("No rating")),
    ("5", "5"),
    ("4", "4"),
    ("3", "3"),
    ("2", "2"),
    ("1", "1"),
)


class ReviewForm(forms.ModelForm):
    """Field validation only. The antispam layers live in the view."""

    class Meta:
        model = Review
        fields = ("author_name", "text_uk", "rating", "photo", "contact_phone", "consent")

    def clean_author_name(self) -> str:
        name = (self.cleaned_data.get("author_name") or "").strip()
        if not name:
            raise forms.ValidationError(_("Tell us how to sign the review."))
        return name

    def clean_text_uk(self) -> str:
        text = (self.cleaned_data.get("text_uk") or "").strip()
        if not text:
            raise forms.ValidationError(_("Write a few words about the flowers."))
        return text

    def clean_rating(self) -> int | None:
        rating = self.cleaned_data.get("rating")
        if rating is None:
            return None
        if not 1 <= int(rating) <= 5:
            raise forms.ValidationError(_("The rating goes from 1 to 5."))
        return int(rating)

    def clean_consent(self) -> bool:
        if not self.cleaned_data.get("consent"):
            raise forms.ValidationError(_("We need your consent to publish the review."))
        return True
