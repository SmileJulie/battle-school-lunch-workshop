from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_neis_client
from app.schemas import Meal, School


class FakeNeisClient:
    async def search_schools(self, query: str) -> tuple[list[School], bool]:
        assert query == "서울"
        return [
            School(
                officeCode="B10",
                schoolCode="7010057",
                name="서울고등학교",
                officeName="서울특별시교육청",
                regionName="서울특별시",
                schoolType="고등학교",
            )
        ], True

    async def get_lunches(
        self,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[Meal]:
        assert office_code == "B10"
        assert school_code == "7010057"
        assert from_ymd == "20260814"
        assert to_ymd == "20260814"
        return [
            Meal(
                date="2026-08-14",
                mealType="중식",
                dishes=["쌀밥", "미역국"],
                calories="650.0 Kcal",
            )
        ]


@pytest.fixture
def client() -> AsyncIterator[TestClient]:
    app.dependency_overrides[get_neis_client] = lambda: FakeNeisClient()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_has_minimal_response(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_search_schools_returns_contract_response(client: TestClient) -> None:
    response = client.get("/api/schools", params={"query": " 서울 "})

    assert response.status_code == 200
    assert response.json()["hasMore"] is True
    assert response.json()["schools"][0]["name"] == "서울고등학교"


def test_get_meals_returns_lunch_only_response(client: TestClient) -> None:
    response = client.get(
        "/api/meals",
        params={
            "officeCode": "B10",
            "schoolCode": "7010057",
            "from": "2026-08-14",
            "to": "2026-08-14",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["school"] == {"officeCode": "B10", "schoolCode": "7010057"}
    assert body["meals"][0]["mealType"] == "중식"


def test_invalid_date_range_does_not_call_upstream(client: TestClient) -> None:
    response = client.get(
        "/api/meals",
        params={
            "officeCode": "B10",
            "schoolCode": "7010057",
            "from": "2026-09-01",
            "to": "2026-08-01",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"
