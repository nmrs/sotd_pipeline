from __future__ import annotations

import calendar
import re
from datetime import date as _date
from typing import Optional

# ------------------------------------------------------------------ #
# Lookup tables and regex patterns                                   #
# ------------------------------------------------------------------ #

_MONTH_NAME_TO_NUM = {name.lower(): idx for idx, name in enumerate(calendar.month_name) if name}
_MONTH_ABBR_TO_NUM = {abbr.lower(): idx for idx, abbr in enumerate(calendar.month_abbr) if abbr}
_MONTH_LOOKUP: dict[str, int] = {**_MONTH_NAME_TO_NUM, **_MONTH_ABBR_TO_NUM}

_MONTH_DAY_RX = re.compile(
    r"\b(?P<month>[A-Za-z]{3,9})\s+(?P<day>\d{1,2})\b(?:[,\s]+(?P<year>\d{4}))?",
    re.IGNORECASE,
)

_SLASH_RX = re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{4}))?")

# Accept: "6 Oct 2021", "(6 Oct 2021)", " 10 Sep 2022 "
_DAY_MONTH_YEAR_RX = re.compile(
    r"\(?\s*(?P<day>\d{1,2})\s+(?P<month>\w{3,9})\.?,?\s+(?P<year>\d{4})\s*\)?"
)

# Accept: "25. June" (day. month format without year)
_DAY_MONTH_RX = re.compile(r"\b(?P<day>\d{1,2})\.\s+(?P<month>\w{3,9})\b")

# ------------------------------------------------------------------ #
# Helper to safely build a date                                      #
# ------------------------------------------------------------------ #


def _build_date(day: int, month: int, year: int) -> Optional[_date]:  # noqa: D401
    """Return a valid date or None if the combination is invalid."""
    try:
        return _date(year, month, day)
    except ValueError:
        return None


def parse_thread_date(title: str, year_hint: int) -> Optional[_date]:
    """
    Extract a calendar date from *title*.

    Matches:
    • Month‑name formats with a day ("May 20, 2025", "Jun 3")
    • Numeric formats ("5/12", "05/12/2025")

    Ignores:
    • Titles without a day element (e.g. "April 2020")
    """
    title_l = title.lower()

    # -------- month‑name or abbreviation ---------------------------- #
    for m in _MONTH_DAY_RX.finditer(title_l):
        month_token = m.group("month").lower()
        month_num = _MONTH_LOOKUP.get(month_token)
        if not month_num:
            continue
        day = int(m.group("day"))
        if not (1 <= day <= 31):
            continue
        year = int(m.group("year")) if m.group("year") else year_hint
        parsed = _build_date(day, month_num, year)
        if parsed:
            return parsed

    # -------- numeric  --------------------------------------------- #
    if m := _SLASH_RX.search(title_l):
        month_num = int(m.group("month"))
        day = int(m.group("day"))
        if not (1 <= month_num <= 12 and 1 <= day <= 31):
            return None
        year = int(m.group("year")) if m.group("year") else year_hint
        return _build_date(day, month_num, year)

    # -------- day month year, parens optional, year required ------------ #
    if m := _DAY_MONTH_YEAR_RX.search(title_l):
        day = int(m.group("day"))
        month_token = m.group("month").lower().rstrip(".")
        month_num = _MONTH_LOOKUP.get(month_token)
        if not month_num or not (1 <= day <= 31):
            return None
        year = int(m.group("year"))
        return _build_date(day, month_num, year)

    # -------- day month format (without year) ------------ #
    if m := _DAY_MONTH_RX.search(title_l):
        day = int(m.group("day"))
        month_token = m.group("month").lower().rstrip(".")
        month_num = _MONTH_LOOKUP.get(month_token)
        if not month_num or not (1 <= day <= 31):
            return None
        # Use year_hint since no year is specified in the title
        return _build_date(day, month_num, year_hint)

    return None
