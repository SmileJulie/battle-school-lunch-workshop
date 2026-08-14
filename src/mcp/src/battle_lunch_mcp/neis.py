import re
from html import unescape
from typing import Any

import httpx

from battle_lunch_mcp.config import Settings
from battle_lunch_mcp.errors import UpstreamError, UpstreamUnavailable

EMPTY_RESULT_CODES = {"INFO-200"}
ERROR_STATUS_CODES = {"ERROR-300", "ERROR-290", "ERROR-310", "ERROR-333", "ERROR-336", "ERROR-337"}
SERVER_ERROR_CODES = {"ERROR-500", "ERROR-600", "ERROR-601"}


class NeisClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def search_schools(self, query: str) -> dict[str, Any]:
        payload = await self._get(
            "/schoolInfo",
            {"SCHUL_NM": query, "pIndex": "1", "pSize": "20"},
        )
        rows, total_count = extract_rows(payload, "schoolInfo")
        schools = [
            {
                "officeCode": require_text(row, "ATPT_OFCDC_SC_CODE"),
                "schoolCode": require_text(row, "SD_SCHUL_CODE"),
                "name": require_text(row, "SCHUL_NM"),
                "officeName": text_or_default(row, "ATPT_OFCDC_SC_NM"),
                "regionName": text_or_default(row, "LCTN_SC_NM"),
                "schoolType": text_or_default(row, "SCHUL_KND_SC_NM"),
            }
            for row in rows[:20]
        ]
        return {
            "status": "success" if schools else "empty",
            "message": None if schools else "일치하는 학교가 없습니다.",
            "schools": schools,
            "hasMore": total_count > 20,
        }

    async def get_lunches(
        self,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> dict[str, Any]:
        page = 1
        collected: dict[tuple[str, str, str], dict[str, Any]] = {}
        total_count = 0

        while True:
            payload = await self._get(
                "/mealServiceDietInfo",
                {
                    "ATPT_OFCDC_SC_CODE": office_code,
                    "SD_SCHUL_CODE": school_code,
                    "MMEAL_SC_CODE": "2",
                    "MLSV_FROM_YMD": from_ymd,
                    "MLSV_TO_YMD": to_ymd,
                    "pIndex": str(page),
                    "pSize": "100",
                },
            )
            rows, total_count = extract_rows(payload, "mealServiceDietInfo")
            for row in rows:
                meal = meal_from_row(row)
                collected[(school_code, meal["date"], "2")] = meal
            if len(collected) >= total_count or not rows:
                break
            page += 1

        meals = sorted(collected.values(), key=lambda meal: meal["date"])
        return {
            "status": "success" if meals else "empty",
            "message": None if meals else "선택 기간에 등록된 중식 정보가 없습니다.",
            "school": {"officeCode": office_code, "schoolCode": school_code},
            "meals": meals,
        }

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        request_params = {"Type": "json", **params}
        if self._settings.neis_api_key:
            request_params["KEY"] = self._settings.neis_api_key
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.neis_base_url,
                timeout=self._settings.neis_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.get(path, params=request_params)
                response.raise_for_status()
                data = response.json()
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise UpstreamUnavailable() from exc
        except (httpx.HTTPStatusError, ValueError) as exc:
            raise UpstreamError() from exc

        if not isinstance(data, dict):
            raise UpstreamError()
        return data


def extract_rows(payload: dict[str, Any], section_name: str) -> tuple[list[dict[str, Any]], int]:
    if "RESULT" in payload:
        result = ensure_dict(payload["RESULT"])
        code = str(result.get("CODE", ""))
        if code in EMPTY_RESULT_CODES:
            return [], 0
        raise_for_neis_result(code)

    section = payload.get(section_name)
    if not isinstance(section, list):
        raise UpstreamError()

    total_count = 0
    rows: list[dict[str, Any]] = []
    for entry in section:
        if not isinstance(entry, dict):
            continue
        head = entry.get("head")
        if isinstance(head, list):
            total_count = extract_total_count(head)
            result = extract_result(head)
            if result:
                code = str(result.get("CODE", ""))
                if code in EMPTY_RESULT_CODES:
                    return [], 0
                if code and code != "INFO-000":
                    raise_for_neis_result(code)
        raw_rows = entry.get("row")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))

    return rows, total_count or len(rows)


def extract_total_count(head: list[Any]) -> int:
    for item in head:
        if isinstance(item, dict) and "list_total_count" in item:
            return int(item["list_total_count"])
    return 0


def extract_result(head: list[Any]) -> dict[str, Any] | None:
    for item in head:
        if isinstance(item, dict) and isinstance(item.get("RESULT"), dict):
            return item["RESULT"]
    return None


def raise_for_neis_result(code: str) -> None:
    if code in SERVER_ERROR_CODES:
        raise UpstreamUnavailable()
    if code in ERROR_STATUS_CODES:
        raise UpstreamError("NEIS_UPSTREAM_ERROR", "NEIS 요청을 처리하지 못했습니다.")
    raise UpstreamError()


def ensure_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UpstreamError()
    return value


def require_text(row: dict[str, Any], key: str) -> str:
    value = str(row.get(key, "")).strip()
    if not value:
        raise UpstreamError()
    return value


def text_or_default(row: dict[str, Any], key: str) -> str:
    value = str(row.get(key, "")).strip()
    return value or "제공되지 않음"


def optional_text(row: dict[str, Any], key: str) -> str | None:
    value = str(row.get(key, "")).strip()
    return clean_neis_text(value) if value else None


def meal_from_row(row: dict[str, Any]) -> dict[str, Any]:
    date_value = require_text(row, "MLSV_YMD")
    if not re.fullmatch(r"\d{8}", date_value):
        raise UpstreamError()
    return {
        "date": f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}",
        "mealType": "중식",
        "dishes": split_dishes(require_text(row, "DDISH_NM")),
        "calories": optional_text(row, "CAL_INFO"),
        "nutrition": optional_text(row, "NTR_INFO"),
        "origin": optional_text(row, "ORPLC_INFO"),
        "servings": parse_servings(row.get("MLSV_FGR")),
    }


def split_dishes(value: str) -> list[str]:
    cleaned = clean_neis_text(value)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def clean_neis_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def parse_servings(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError as exc:
        raise UpstreamError() from exc
