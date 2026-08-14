import pytest

from battle_lunch_mcp.errors import UpstreamError
from battle_lunch_mcp.neis import extract_rows, meal_from_row


def test_extract_rows_handles_empty_result_code() -> None:
    rows, total = extract_rows(
        {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
        "schoolInfo",
    )

    assert rows == []
    assert total == 0


def test_meal_from_row_cleans_html() -> None:
    meal = meal_from_row(
        {
            "MLSV_YMD": "20260814",
            "DDISH_NM": "쌀밥<br/>미역국<br>배추김치",
            "CAL_INFO": "650.0 Kcal",
            "NTR_INFO": "탄수화물(g): 90.0<br/>단백질(g): 25.0",
            "ORPLC_INFO": "쌀: 국내산",
            "MLSV_FGR": "500",
        }
    )

    assert meal["date"] == "2026-08-14"
    assert meal["mealType"] == "중식"
    assert meal["dishes"] == ["쌀밥", "미역국", "배추김치"]
    assert meal["nutrition"] == "탄수화물(g): 90.0\n단백질(g): 25.0"
    assert meal["servings"] == 500


def test_missing_required_meal_date_is_upstream_error() -> None:
    with pytest.raises(UpstreamError):
        meal_from_row({"DDISH_NM": "쌀밥"})
