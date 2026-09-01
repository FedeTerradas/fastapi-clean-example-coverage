"""
New tests to improve coverage of UtcDatetime.__lt__ (lines 27-30).

Gap identified by pytest-cov: the __lt__ method and its NotImplemented
branch were not covered by existing tests.
"""

from datetime import UTC, datetime

import pytest

from app.core.common.value_objects.utc_datetime import UtcDatetime


def _make_utc(year: int, month: int, day: int) -> UtcDatetime:
    return UtcDatetime(datetime(year, month, day, tzinfo=UTC))


def test_earlier_utcdatetime_is_less_than_later() -> None:
    """Line 30: covers the `self.value < other.value` branch."""
    earlier = _make_utc(2024, 1, 1)
    later = _make_utc(2024, 6, 1)

    assert earlier < later


def test_later_utcdatetime_is_not_less_than_earlier() -> None:
    """Lines 27-30: covers both isinstance check and comparison returning False."""
    earlier = _make_utc(2024, 1, 1)
    later = _make_utc(2024, 6, 1)

    assert not (later < earlier)


def test_equal_utcdatetimes_are_not_less_than_each_other() -> None:
    """Boundary case: equal values — neither is less than the other."""
    dt = _make_utc(2024, 3, 15)
    same = _make_utc(2024, 3, 15)

    assert not (dt < same)
    assert not (same < dt)


def test_lt_returns_not_implemented_for_incompatible_type() -> None:
    """Lines 28-29: covers the isinstance guard returning NotImplemented.

    Python's @total_ordering relies on __lt__ returning NotImplemented
    when the other operand is of an incompatible type, so this branch
    must be exercised to guarantee correct behavior with third-party types.
    """
    dt = _make_utc(2024, 1, 1)

    with pytest.raises(TypeError):
        _ = dt < "2024-01-01"
