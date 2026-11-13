import pytest

from pipeline.normalize import (
    normalize_header, normalize_phone, parse_date, parse_decimal,
    parse_enum, parse_timestamp,
)


@pytest.mark.parametrize("raw, expected", [
    ("Mobile_No", "mobile no"),
    ("  Policy   No ", "policy no"),
    ("customer__name", "customer name"),
])
def test_normalize_header(raw, expected):
    assert normalize_header(raw) == expected


# The six phone formats seen in the data, plus invalid ones
@pytest.mark.parametrize("raw, expected", [
    ("9932302346", "+919932302346"),
    ("+916463745499", "+916463745499"),
    ("+91 79328 96340", "+917932896340"),
    ("(+91) 9247939334", "+919247939334"),
    ("91-77187-50036", "+917718750036"),
    ("07291535375", "+917291535375"),
    ("993-230-2346", "+919932302346"),
    ("123456789", None),             # 9 digits
    ("5932302346", None),            # starts with 5
    ("N/A", None),
    ("", None),
    (None, None),
])
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2026-11-23", "2026-11-23"),
    ("27/10/2026", "2026-10-27"),
    ("21-11-2026", "2026-11-21"),
    ("01-Dec-2026", "2026-12-01"),
    ("01-dec-2026", "2026-12-01"),
    ("05/11/2026", "2026-11-05"),     # day-first: 5 November, not 11 May
    ("31/02/2026", None),             # impossible date
    ("2026-13-01", None),             # month 13
    ("TBD", None),
    ("", None),
])
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("6850", "6850.00"),
    ("₹27,554", "27554.00"),
    ("INR 25301.4", "25301.40"),
    ("Rs. 24787", "24787.00"),
    ("rs24787", "24787.00"),
    ("4737.145", "4737.15"),          # rounds half up
    ("-500", None),
    ("-", None),
    ("N/A", None),
])
def test_parse_decimal(raw, expected):
    assert parse_decimal(raw) == expected


def test_parse_enum():
    langs = ["en", "hi", "ta"]
    assert parse_enum(" HI ", langs) == "hi"
    assert parse_enum("Hindi", langs) is None


@pytest.mark.parametrize("raw, expected", [
    ("2026-10-05T13:20:21Z", "2026-10-05T18:50:21+05:30"),
    ("2026-10-01T10:40:19+05:30", "2026-10-01T10:40:19+05:30"),
    ("2026-10-03 10:01:00", "2026-10-03T10:01:00+05:30"),   # naive means IST
    ("2026-10-01T20:00:00Z", "2026-10-02T01:30:00+05:30"),  # crosses midnight in IST
])
def test_parse_timestamp(raw, expected):
    assert parse_timestamp(raw).isoformat() == expected


def test_parse_timestamp_invalid():
    assert parse_timestamp("yesterday") is None