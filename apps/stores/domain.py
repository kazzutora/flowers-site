"""Pure domain logic for stores — no Django imports (tech.md §3.1)."""

from __future__ import annotations

from datetime import datetime, time

WorkHours = dict[str, list[str] | None]

_DAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _parse_range(day_range: list[str]) -> tuple[time, time]:
    open_str, close_str = day_range
    open_h, open_m = (int(part) for part in open_str.split(":"))
    close_h, close_m = (int(part) for part in close_str.split(":"))
    return time(open_h, open_m), time(close_h, close_m)


def is_open_now(work_hours: WorkHours, now: datetime) -> bool:
    """True if ``now`` falls inside ``work_hours`` for its weekday.

    ``work_hours`` maps day keys (``"mon"``..``"sun"``) to a
    ``[open, close]`` pair of ``"HH:MM"`` strings, or ``None`` for a day
    off (tech.md §4.1). A range crossing midnight (open > close, e.g.
    ``["20:00", "02:00"]``) stays open past midnight into the next
    calendar day.

    Boundary convention: open is inclusive, close is exclusive — the
    closing minute itself already counts as closed.

    ``now`` must already be an aware datetime localized to the store's
    timezone (Europe/Kyiv, tech.md §4.1) — this function is timezone
    agnostic by design; the caller (apps.stores.selectors) is responsible
    for localizing it.
    """
    today_key = _DAY_KEYS[now.weekday()]
    yesterday_key = _DAY_KEYS[(now.weekday() - 1) % 7]

    today_range = work_hours.get(today_key)
    if today_range:
        open_t, close_t = _parse_range(today_range)
        if open_t <= close_t:
            if open_t <= now.time() < close_t:
                return True
        elif now.time() >= open_t:
            return True

    yesterday_range = work_hours.get(yesterday_key)
    if yesterday_range:
        open_t, close_t = _parse_range(yesterday_range)
        if open_t > close_t and now.time() < close_t:
            return True

    return False
