from typing import Any

import pytest

from battle_lunch_mcp.server import create_mcp


class FakeNeisClient:
    async def search_schools(self, query: str) -> dict[str, Any]:
        assert query == "서울"
        return {
            "status": "success",
            "message": None,
            "schools": [
                {
                    "officeCode": "B10",
                    "schoolCode": "7010057",
                    "name": "서울고등학교",
                    "officeName": "서울특별시교육청",
                    "regionName": "서울특별시",
                    "schoolType": "고등학교",
                }
            ],
            "hasMore": False,
        }

    async def get_lunches(
        self,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> dict[str, Any]:
        assert office_code == "B10"
        assert school_code == "7010057"
        assert from_ymd == "20260814"
        assert to_ymd == "20260814"
        return {
            "status": "success",
            "message": None,
            "school": {"officeCode": office_code, "schoolCode": school_code},
            "meals": [{"date": "2026-08-14", "mealType": "중식", "dishes": ["쌀밥"]}],
        }


@pytest.mark.asyncio
async def test_mcp_client_can_list_school_lunch_tools() -> None:
    mcp = create_mcp(client=FakeNeisClient())

    tools = await mcp.list_tools()

    assert {tool.name for tool in tools} == {"search_schools", "get_lunch_menus"}


@pytest.mark.asyncio
async def test_mcp_tools_call_neis_client_with_validated_arguments() -> None:
    mcp = create_mcp(client=FakeNeisClient())

    school_result = await mcp.call_tool("search_schools", {"query": " 서울 "})
    meal_result = await mcp.call_tool(
        "get_lunch_menus",
        {
            "officeCode": "B10",
            "schoolCode": "7010057",
            "fromDate": "2026-08-14",
            "toDate": "2026-08-14",
        },
    )

    _, structured_school_result = school_result
    _, structured_meal_result = meal_result

    assert structured_school_result["schools"][0]["name"] == "서울고등학교"
    assert structured_meal_result["meals"][0]["mealType"] == "중식"
    assert structured_meal_result["from"] == "2026-08-14"
