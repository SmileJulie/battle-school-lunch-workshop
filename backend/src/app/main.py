import logging
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .clients.neis import NeisClient
from .config import Settings, get_settings
from .errors import ApiError, UpstreamError
from .schemas import HealthResponse, MealSearchResponse, SchoolRef, SchoolSearchResponse
from .validation import (
    to_neis_date,
    validate_date_range,
    validate_school_code,
    validate_school_query,
)

logger = logging.getLogger("battle_school_lunch")


settings = get_settings()
app = FastAPI(title="급식 배틀 API", version="1.0.0")
app.state.settings = settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        },
    )
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "requestId": getattr(request.state, "request_id", str(uuid4())),
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unexpected error",
        extra={"request_id": getattr(request.state, "request_id", "unknown")},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "요청을 처리하지 못했습니다.",
                "requestId": getattr(request.state, "request_id", str(uuid4())),
            }
        },
    )


def get_current_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_current_settings)]


def get_neis_client(settings: SettingsDep) -> NeisClient:
    return NeisClient(settings)


NeisClientDep = Annotated[NeisClient, Depends(get_neis_client)]
SchoolQuery = Annotated[str, Query(min_length=1, max_length=100)]
RequiredQuery = Annotated[str, Query()]
FromDateQuery = Annotated[str, Query(alias="from")]


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/schools", response_model=SchoolSearchResponse)
async def search_schools(
    query: SchoolQuery,
    client: NeisClientDep,
) -> SchoolSearchResponse:
    normalized_query = validate_school_query(query)
    schools, has_more = await client.search_schools(normalized_query)
    return SchoolSearchResponse(schools=schools, hasMore=has_more)


@app.get("/api/meals", response_model=MealSearchResponse)
async def get_meals(
    officeCode: RequiredQuery,
    schoolCode: RequiredQuery,
    from_: FromDateQuery,
    to: RequiredQuery,
    client: NeisClientDep,
) -> MealSearchResponse:
    office_code = validate_school_code(officeCode, "교육청 코드")
    school_code = validate_school_code(schoolCode, "학교 코드")
    from_date, to_date = validate_date_range(from_, to)
    try:
        meals = await client.get_lunches(
            office_code,
            school_code,
            to_neis_date(from_date),
            to_neis_date(to_date),
        )
    except ApiError:
        raise
    except Exception as exc:
        raise UpstreamError() from exc
    return MealSearchResponse(
        school=SchoolRef(officeCode=office_code, schoolCode=school_code),
        from_=from_date.isoformat(),
        to=to_date.isoformat(),
        meals=meals,
    )
