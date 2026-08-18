"""Due dates.

The date that matters most here is the one everyone gets wrong: a foreign corporation
with no U.S. office files Form 1120-F on the 15th day of the *6th* month, not the 4th.
"""

from __future__ import annotations

from datetime import date, timedelta


def _weekday_safe(d: date) -> date:
    """Push Saturday/Sunday to the following Monday (IRC §7503)."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def form_due_date(form: str, tax_year: int, *, foreign_no_us_office: bool = True) -> date:
    """Original due date for a calendar-year filer."""
    y = tax_year + 1
    match form:
        case "1120-F":
            # Reg. §1.6072-2(b): 15th day of the 6th month where the foreign corporation
            # has no office or place of business in the United States.
            return _weekday_safe(date(y, 6, 15) if foreign_no_us_office else date(y, 4, 15))
        case "1065" | "8865":
            return _weekday_safe(date(y, 3, 15))
        case "8804" | "8805":
            return _weekday_safe(date(y, 3, 15))
        case "1120" | "5472":
            return _weekday_safe(date(y, 4, 15))
        case "1040-NR":
            return _weekday_safe(date(y, 6, 15))
        case "1042" | "1042-S":
            return _weekday_safe(date(y, 3, 15))
        case _:
            return _weekday_safe(date(y, 4, 15))


def extended_due_date(form: str, tax_year: int, *, foreign_no_us_office: bool = True) -> date:
    """Due date after a timely Form 7004 (or 4868 equivalent)."""
    y = tax_year + 1
    match form:
        case "1120-F":
            return _weekday_safe(date(y, 12, 15) if foreign_no_us_office else date(y, 10, 15))
        case "1065" | "8865":
            return _weekday_safe(date(y, 9, 15))
        case "8804" | "8805":
            return _weekday_safe(date(y, 9, 15))
        case "1120" | "5472":
            return _weekday_safe(date(y, 10, 15))
        case "1040-NR":
            return _weekday_safe(date(y, 12, 15))
        case _:
            return _weekday_safe(date(y, 10, 15))


def state_due_date(state: str, tax_year: int) -> date:
    """State original due dates for the states multifamily syndications concentrate in."""
    y = tax_year + 1
    match state:
        case "TX":
            return _weekday_safe(date(y, 5, 15))    # franchise report
        case "TN":
            return _weekday_safe(date(y, 4, 15))    # F&E
        case "FL":
            return _weekday_safe(date(y, 5, 1))     # F-1120
        case _:
            return _weekday_safe(date(y, 4, 15))
