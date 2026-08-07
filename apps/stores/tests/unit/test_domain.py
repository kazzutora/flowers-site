"""Boundary tests for is_open_now, per DEV.md S0.9: minute before opening,
minute after closing, day off, midnight crossing.

Dates are picked via ``date.fromisocalendar`` (fixed ISO week 32 / 2026)
so each test names the weekday it means (1=Monday..7=Sunday) instead of
depending on knowing what weekday an arbitrary calendar date falls on.
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from apps.stores.domain import is_open_now

KYIV = ZoneInfo("Europe/Kyiv")

WORK_HOURS = {
    "mon": ["09:00", "20:00"],
    "tue": ["09:00", "20:00"],
    "wed": ["09:00", "20:00"],
    "thu": ["09:00", "20:00"],
    "fri": ["09:00", "20:00"],
    "sat": ["10:00", "18:00"],
    "sun": None,
}


def _at(iso_weekday: int, hour: int, minute: int) -> datetime:
    day = date.fromisocalendar(2026, 32, iso_weekday)
    return datetime.combine(day, time(hour, minute), tzinfo=KYIV)


def test_minute_before_opening_is_closed() -> None:
    assert is_open_now(WORK_HOURS, _at(1, 8, 59)) is False


def test_at_opening_minute_is_open() -> None:
    assert is_open_now(WORK_HOURS, _at(1, 9, 0)) is True


def test_minute_before_closing_is_open() -> None:
    assert is_open_now(WORK_HOURS, _at(1, 19, 59)) is True


def test_at_closing_minute_is_closed() -> None:
    assert is_open_now(WORK_HOURS, _at(1, 20, 0)) is False


def test_minute_after_closing_is_closed() -> None:
    assert is_open_now(WORK_HOURS, _at(1, 20, 1)) is False


def test_day_off_is_always_closed() -> None:
    assert is_open_now(WORK_HOURS, _at(7, 0, 0)) is False
    assert is_open_now(WORK_HOURS, _at(7, 12, 0)) is False
    assert is_open_now(WORK_HOURS, _at(7, 23, 59)) is False


def test_midnight_crossing_open_before_midnight() -> None:
    hours = {**WORK_HOURS, "fri": ["20:00", "02:00"]}
    assert is_open_now(hours, _at(5, 21, 0)) is True


def test_midnight_crossing_open_just_after_midnight() -> None:
    hours = {**WORK_HOURS, "fri": ["20:00", "02:00"]}
    assert is_open_now(hours, _at(6, 0, 30)) is True


def test_midnight_crossing_closed_at_and_after_close() -> None:
    hours = {**WORK_HOURS, "fri": ["20:00", "02:00"], "sat": None}
    assert is_open_now(hours, _at(6, 2, 0)) is False
    assert is_open_now(hours, _at(6, 3, 0)) is False


def test_midnight_crossing_does_not_shadow_next_days_own_hours() -> None:
    hours = {**WORK_HOURS, "fri": ["20:00", "02:00"]}
    assert is_open_now(hours, _at(6, 12, 0)) is True  # Saturday's own 10-18
    assert is_open_now(hours, _at(6, 19, 0)) is False  # after Saturday's own close
