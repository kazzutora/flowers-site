"""tech.md §1.1 fixed sitemap + §8: nav is data, layout renders it in a
loop. Adding a menu item is a one-line edit here, never a template edit.

URLs are literal strings, not ``reverse()`` lookups: the sitemap is frozen
core content and several targets (catalog, constructor, live, gallery,
cart, reviews) belong to apps that don't exist until later stages. Linking
to their frozen, already-decided path costs nothing today and needs no
edit when that app lands.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    url: str


MAIN_NAV: list[NavItem] = [
    NavItem(key="catalog", label="Каталог", url="/catalog/"),
    NavItem(key="constructor", label="Конструктор", url="/constructor/"),
    NavItem(key="live", label="Наживо з магазину", url="/live/"),
    NavItem(key="gallery", label="Галерея робіт", url="/gallery/"),
    NavItem(key="stores", label="Наші магазини", url="/stores/"),
    NavItem(key="payment-delivery", label="Оплата і отримання", url="/payment-delivery/"),
    NavItem(key="reviews", label="Відгуки", url="/reviews/"),
    NavItem(key="contacts", label="Контакти", url="/contacts/"),
]
