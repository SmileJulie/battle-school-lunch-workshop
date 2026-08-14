from mcp.server.fastmcp.exceptions import ToolError


class UserInputError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class UpstreamError(Exception):
    def __init__(
        self,
        code: str = "NEIS_UPSTREAM_ERROR",
        message: str = "NEIS 응답을 처리하지 못했습니다.",
    ) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class UpstreamUnavailable(UpstreamError):
    def __init__(self, message: str = "NEIS 응답이 지연되었거나 연결할 수 없습니다.") -> None:
        super().__init__("NEIS_UPSTREAM_UNAVAILABLE", message)


def as_tool_error(exc: Exception) -> ToolError:
    if isinstance(exc, UserInputError | UpstreamError):
        return ToolError(f"{exc.code}: {exc.message}")
    return ToolError("INTERNAL_ERROR: MCP 도구 실행 중 오류가 발생했습니다.")
