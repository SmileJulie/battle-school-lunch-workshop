import re
from datetime import date

from battle_lunch_mcp.errors import UserInputError

CODE_RE = re.compile(r"^[A-Z0-9]{1,20}$")
MAX_RANGE_DAYS = 31


def validate_school_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise UserInputError("INVALID_SCHOOL_QUERY", "학교명을 입력해 주세요.")
    if len(normalized) > 100:
        raise UserInputError("INVALID_SCHOOL_QUERY", "학교명은 100자 이하로 입력해 주세요.")
    return normalized


def validate_school_code(value: str, label: str) -> str:
    normalized = value.strip()
    if not CODE_RE.fullmatch(normalized):
        raise UserInputError("INVALID_SCHOOL_CODE", f"{label} 형식이 올바르지 않습니다.")
    return normalized


def parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise UserInputError("INVALID_DATE", f"{label} 날짜 형식은 YYYY-MM-DD여야 합니다.") from exc


def validate_date_range(from_value: str, to_value: str) -> tuple[date, date]:
    from_date = parse_date(from_value, "시작일")
    to_date = parse_date(to_value, "종료일")
    if from_date > to_date:
        raise UserInputError("INVALID_DATE_RANGE", "시작일은 종료일보다 늦을 수 없습니다.")
    if (to_date - from_date).days + 1 > MAX_RANGE_DAYS:
        raise UserInputError("INVALID_DATE_RANGE", "조회 기간은 최대 31일까지 가능합니다.")
    return from_date, to_date


def to_neis_date(value: date) -> str:
    return value.strftime("%Y%m%d")
