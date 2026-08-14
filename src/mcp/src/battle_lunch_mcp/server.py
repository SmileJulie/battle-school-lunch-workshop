from typing import Any

from mcp.server.fastmcp import FastMCP

from battle_lunch_mcp.config import Settings, load_settings
from battle_lunch_mcp.errors import UpstreamError, UserInputError, as_tool_error
from battle_lunch_mcp.neis import NeisClient
from battle_lunch_mcp.validation import (
    to_neis_date,
    validate_date_range,
    validate_school_code,
    validate_school_query,
)


def create_mcp(client: NeisClient | None = None, settings: Settings | None = None) -> FastMCP:
    resolved_settings = settings or load_settings()
    neis_client = client or NeisClient(resolved_settings)
    mcp = FastMCP(
        "battle-school-lunch",
        instructions=(
            "NEIS 공개 API를 사용해 학교 후보와 날짜별 중식 정보를 조회합니다. "
            "학교 검색 후 officeCode와 schoolCode를 급식 조회 도구에 전달하세요."
        ),
        host=resolved_settings.mcp_host,
        port=resolved_settings.mcp_port,
        streamable_http_path=resolved_settings.mcp_path,
    )

    @mcp.tool(
        name="search_schools",
        description="학교 이름 일부로 NEIS 학교 후보를 최대 20개까지 조회합니다.",
    )
    async def search_schools(query: str) -> dict[str, Any]:
        try:
            normalized_query = validate_school_query(query)
            return await neis_client.search_schools(normalized_query)
        except (UserInputError, UpstreamError) as exc:
            raise as_tool_error(exc) from exc

    @mcp.tool(
        name="get_lunch_menus",
        description=(
            "선택한 학교의 시작일과 종료일을 포함한 기간 중식 정보를 조회합니다. "
            "날짜 형식은 YYYY-MM-DD이고 조회 기간은 최대 31일입니다."
        ),
    )
    async def get_lunch_menus(
        officeCode: str,
        schoolCode: str,
        fromDate: str,
        toDate: str,
    ) -> dict[str, Any]:
        try:
            office_code = validate_school_code(officeCode, "교육청 코드")
            school_code = validate_school_code(schoolCode, "학교 코드")
            from_date, to_date = validate_date_range(fromDate, toDate)
            response = await neis_client.get_lunches(
                office_code,
                school_code,
                to_neis_date(from_date),
                to_neis_date(to_date),
            )
            response["from"] = fromDate
            response["to"] = toDate
            return response
        except (UserInputError, UpstreamError) as exc:
            raise as_tool_error(exc) from exc

    return mcp


def main() -> None:
    create_mcp().run(transport="streamable-http")


if __name__ == "__main__":
    main()
