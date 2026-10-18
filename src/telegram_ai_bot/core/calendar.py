"""Date helpers. The model gets the current date so it can resolve "tomorrow", weekdays, etc."""

from datetime import datetime

_DAYS_BEFORE_MONTH = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def to_jalali(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert a Gregorian date to the Jalali (Solar Hijri) calendar."""
    gy2 = year + 1 if month > 2 else year
    days = (
        355666
        + 365 * year
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        + day
        + _DAYS_BEFORE_MONTH[month - 1]
    )
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30


def describe_now(now: datetime | None = None) -> str:
    now = now or datetime.now()
    jy, jm, jd = to_jalali(now.year, now.month, now.day)
    return f"{now:%A}, {now:%Y-%m-%d %H:%M} (Jalali {jy}/{jm:02d}/{jd:02d})"
