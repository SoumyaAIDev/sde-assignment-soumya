"""Small, pure functions that clean one raw value at a time.

Every parser returns the cleaned value, or None if the value is invalid.
They never raise, so the caller decides what "invalid" means for a row.
"""
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

IST = timezone(timedelta(hours=5, minutes=30))

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def normalize_header(header: str) -> str:
    """'  Mobile_No ' -> 'mobile no'"""
    return re.sub(r"[_\s]+", " ", header.strip().lower())


def normalize_phone(raw: str | None) -> str | None:
    """Return '+91XXXXXXXXXX' for a valid Indian mobile number, else None."""
    if raw is None:
        return None
    digits = re.sub(r"\D", "", raw)          # keep only 0-9
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    return None


def parse_date(raw: str) -> str | None:
    """Accept YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD-Mon-YYYY. Return 'YYYY-MM-DD'."""
    raw = raw.strip()
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", raw):
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
    elif m := re.fullmatch(r"(\d{2})[/-](\d{2})[/-](\d{4})", raw):
        if raw[2] != raw[5]:                  # reject mixed separators like 01/12-2026
            return None
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
    elif m := re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", raw):
        mo = MONTHS.get(m[2].lower())
        if mo is None:
            return None
        d, y = int(m[1]), int(m[3])
    else:
        return None
    try:
        return date(y, mo, d).isoformat()     # date() rejects 31/02, month 13, etc.
    except ValueError:
        return None


def parse_decimal(raw: str) -> str | None:
    """'₹27,554' / 'Rs. 24787' / 'INR 25301.4' -> '27554.00'. Must be >= 0."""
    text = re.sub(r"^(₹|rs\.?|inr)\s*", "", raw.strip(), flags=re.IGNORECASE)
    text = text.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", text):  # no minus sign allowed, so >= 0 is guaranteed
        return None
    try:
        value = Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None
    return str(value)


def parse_enum(raw: str, allowed: list[str]) -> str | None:
    value = raw.strip().lower()
    return value if value in {a.lower() for a in allowed} else None


def parse_timestamp(raw: str) -> datetime | None:
    """Parse '...Z', '...+05:30' or naive '2026-10-03 10:01:00' (naive = IST).

    Always returns a timezone-aware datetime converted to IST.
    """
    try:
        dt = datetime.fromisoformat(raw.strip())   # Python 3.11+ understands 'Z'
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST)