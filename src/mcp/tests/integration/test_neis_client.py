import httpx
import pytest

from battle_lunch_mcp.config import Settings
from battle_lunch_mcp.errors import UpstreamUnavailable
from battle_lunch_mcp.neis import NeisClient


@pytest.mark.asyncio
async def test_search_schools_sends_expected_neis_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/schoolInfo"
        params = dict(request.url.params)
        assert params["Type"] == "json"
        assert params["SCHUL_NM"] == "서울"
        assert params["pIndex"] == "1"
        assert params["pSize"] == "20"
        return httpx.Response(
            200,
            json={
                "schoolInfo": [
                    {"head": [{"list_total_count": 1}, {"RESULT": {"CODE": "INFO-000"}}]},
                    {
                        "row": [
                            {
                                "ATPT_OFCDC_SC_CODE": "B10",
                                "SD_SCHUL_CODE": "7010057",
                                "SCHUL_NM": "서울고등학교",
                            }
                        ]
                    },
                ]
            },
        )

    client = NeisClient(Settings(neis_base_url="https://neis.test"), httpx.MockTransport(handler))

    result = await client.search_schools("서울")

    assert result["status"] == "success"
    assert result["schools"][0]["officeName"] == "제공되지 않음"


@pytest.mark.asyncio
async def test_get_lunches_uses_lunch_code_and_dates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        assert request.url.path == "/mealServiceDietInfo"
        assert params["MMEAL_SC_CODE"] == "2"
        assert params["MLSV_FROM_YMD"] == "20260814"
        assert params["MLSV_TO_YMD"] == "20260814"
        return httpx.Response(
            200,
            json={
                "mealServiceDietInfo": [
                    {"head": [{"list_total_count": 1}, {"RESULT": {"CODE": "INFO-000"}}]},
                    {"row": [{"MLSV_YMD": "20260814", "DDISH_NM": "쌀밥<br/>미역국"}]},
                ]
            },
        )

    client = NeisClient(Settings(neis_base_url="https://neis.test"), httpx.MockTransport(handler))

    result = await client.get_lunches("B10", "7010057", "20260814", "20260814")

    assert result["meals"][0]["dishes"] == ["쌀밥", "미역국"]


@pytest.mark.asyncio
async def test_timeout_is_mapped_to_safe_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("secret url timed out", request=request)

    client = NeisClient(Settings(neis_base_url="https://neis.test"), httpx.MockTransport(handler))

    with pytest.raises(UpstreamUnavailable, match="NEIS"):
        await client.search_schools("서울")
