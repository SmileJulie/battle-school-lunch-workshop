from dataclasses import dataclass


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str


class InvalidRequest(ApiError):
    def __init__(self, message: str, code: str = "INVALID_REQUEST") -> None:
        super().__init__(400, code, message)


class UpstreamError(ApiError):
    def __init__(self, message: str = "외부 서비스 응답을 처리하지 못했습니다.") -> None:
        super().__init__(502, "UPSTREAM_ERROR", message)


class UpstreamUnavailable(ApiError):
    def __init__(self, message: str = "급식 정보를 불러오지 못했습니다.") -> None:
        super().__init__(503, "UPSTREAM_UNAVAILABLE", message)
