"""The two ways into the same model: "call me back" and the full enquiry."""

from typing import Any

import phonenumbers
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.leads.models import Lead

REGION = "UA"


def normalize_phone(raw: str) -> str:
    """A Ukrainian number in E.164, or an empty string when it is not one.

    Idempotent: feeding the result back in returns the same string.
    """
    try:
        parsed = phonenumbers.parse(raw, REGION)
    except phonenumbers.NumberParseException:
        return ""
    if not phonenumbers.is_valid_number(parsed):
        return ""
    return str(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))


class BaseLeadForm(forms.ModelForm):
    """Field validation only. The antispam layers live in the view."""

    class Meta:
        model = Lead
        fields = ("name", "phone", "consent")

    def clean_name(self) -> str:
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError(_("Tell us how to address you."))
        return name

    def clean_phone(self) -> str:
        normalized = normalize_phone(str(self.data.get("phone") or ""))
        if not normalized:
            raise forms.ValidationError(_("Check the number: 0501234567 or +380501234567."))
        return normalized

    def clean_consent(self) -> bool:
        if not self.cleaned_data.get("consent"):
            raise forms.ValidationError(_("We need your consent to call you back."))
        return True


class CallbackForm(BaseLeadForm):
    """ "Call me back": a name and a number, nothing else to type on a phone."""


class LeadForm(BaseLeadForm):
    class Meta(BaseLeadForm.Meta):
        # The full form; the short one keeps the three fields of the base.
        fields = (  # type: ignore[assignment]
            "name",
            "phone",
            "preferred_contact",
            "event_date",
            "budget_text",
            "comment",
            "consent",
        )
        widgets = {"event_date": forms.DateInput(attrs={"type": "date"})}

    def clean_event_date(self) -> Any:
        return self.cleaned_data.get("event_date")


FORMS: dict[str, type[BaseLeadForm]] = {"callback": CallbackForm, "full": LeadForm}


def form_for(kind: str) -> type[BaseLeadForm]:
    return FORMS.get(kind, LeadForm)
