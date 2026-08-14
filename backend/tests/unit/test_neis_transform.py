import pytest

from app.clients.neis import extract_rows, meal_from_row
from app.errors import UpstreamError


def test_extract_rows_handles_empty_result_code() -> None:
    rows, total = extract_rows(
        {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
        "schoolInfo",
    )

    assert rows == []
    assert total == 0


def test_meal_from_row_cleans_html_and_sorts_fields() -> None:
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

    assert meal.date == "2026-08-14"
    assert meal.mealType == "중식"
    assert meal.dishes == ["쌀밥", "미역국", "배추김치"]
    assert meal.nutrition == "탄수화물(g): 90.0\n단백질(g): 25.0"
    assert meal.servings == 500


def test_meal_from_row_accepts_decimal_servings() -> None:
    meal = meal_from_row(
        {
            "MLSV_YMD": "20240603",
            "DDISH_NM": "찰옥수수밥",
            "MLSV_FGR": 808.00,
        }
    )

    assert meal.servings == 808


def test_missing_required_meal_date_is_upstream_error() -> None:
    with pytest.raises(UpstreamError):
        meal_from_row({"DDISH_NM": "쌀밥"})
