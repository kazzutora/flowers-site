"""Menu items as data.

Adding an entry never touches a template. Entries whose view has not landed yet
are skipped instead of breaking the header.
"""

from dataclasses import dataclass, field

from django.urls import NoReverseMatch, reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class NavItem:
    # Lazy: the label is translated per request, not at import time.
    label: str | Promise
    url_name: str
    kwargs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedNavItem:
    label: str
    url: str


MAIN_MENU: tuple[NavItem, ...] = (
    NavItem(_("Gallery"), "gallery"),
    NavItem(_("About"), "static_page", {"slug": "pro-nas"}),
    NavItem(_("Delivery and payment"), "static_page", {"slug": "dostavka-i-oplata"}),
    NavItem(_("Reviews"), "review_list"),
    NavItem(_("Blog"), "post_list"),
    NavItem(_("Contacts"), "contacts"),
)

FOOTER_MENU: tuple[NavItem, ...] = (
    NavItem(_("Gallery"), "gallery"),
    NavItem(_("About"), "static_page", {"slug": "pro-nas"}),
    NavItem(_("Delivery and payment"), "static_page", {"slug": "dostavka-i-oplata"}),
    NavItem(_("Questions and answers"), "static_page", {"slug": "faq"}),
    NavItem(_("Reviews"), "review_list"),
    NavItem(_("Blog"), "post_list"),
    NavItem(_("Contacts"), "contacts"),
    NavItem(_("Privacy policy"), "static_page", {"slug": "polityka-konfidentsiynosti"}),
)


def resolve(items: tuple[NavItem, ...]) -> list[ResolvedNavItem]:
    resolved: list[ResolvedNavItem] = []
    for item in items:
        try:
            url = reverse(item.url_name, kwargs=item.kwargs or None)
        except NoReverseMatch:
            continue
        resolved.append(ResolvedNavItem(label=str(item.label), url=url))
    return resolved


def main_items() -> list[ResolvedNavItem]:
    return resolve(MAIN_MENU)


def footer_items() -> list[ResolvedNavItem]:
    return resolve(FOOTER_MENU)
