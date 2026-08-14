import pytest

from battle_lunch_mcp.errors import UserInputError
from battle_lunch_mcp.validation import (
    to_neis_date,
    validate_date_range,
    validate_school_code,
    validate_school_query,
)


def test_validate_school_query_trims_input() -> None:
    assert validate_school_query(" 서울 ") == "서울"


def test_blank_school_query_is_rejected() -> None:
    with pytest.raises(UserInputError, match="학교명"):
        validate_school_query("  ")


def test_validate_school_code_rejects_unsafe_value() -> None:
    with pytest.raises(UserInputError, match="형식"):
        validate_school_code("../secret", "학교 코드")


def test_validate_date_range_limits_to_31_days() -> None:
    with pytest.raises(UserInputError, match="31"):
        validate_date_range("2026-08-01", "2026-09-01")


def test_validate_date_range_converts_to_neis_date() -> None:
    from_date, to_date = validate_date_range("2026-08-14", "2026-08-15")

    assert to_neis_date(from_date) == "20260814"
    assert to_neis_date(to_date) == "20260815"
