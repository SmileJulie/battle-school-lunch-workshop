import pytest

from app.errors import InvalidRequest
from app.validation import to_neis_date, validate_date_range, validate_school_query


def test_school_query_is_trimmed() -> None:
    assert validate_school_query(" 서울고 ") == "서울고"


def test_blank_school_query_is_invalid() -> None:
    with pytest.raises(InvalidRequest):
        validate_school_query("   ")


def test_date_range_is_inclusive_and_limited_to_31_days() -> None:
    from_date, to_date = validate_date_range("2026-08-01", "2026-08-31")

    assert to_neis_date(from_date) == "20260801"
    assert to_neis_date(to_date) == "20260831"


def test_reversed_date_range_is_invalid() -> None:
    with pytest.raises(InvalidRequest) as error:
        validate_date_range("2026-08-15", "2026-08-14")

    assert error.value.code == "INVALID_DATE_RANGE"


def test_date_range_over_31_days_is_invalid() -> None:
    with pytest.raises(InvalidRequest):
        validate_date_range("2026-08-01", "2026-09-01")
