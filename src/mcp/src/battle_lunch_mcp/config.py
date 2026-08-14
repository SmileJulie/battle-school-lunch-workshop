import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    neis_api_key: str | None = None
    neis_base_url: str = "https://open.neis.go.kr/hub"
    neis_timeout_seconds: float = 5.0
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    mcp_path: str = "/mcp"


def load_settings() -> Settings:
    api_key = os.getenv("NEIS_API_KEY", "").strip() or None
    return Settings(
        neis_api_key=api_key,
        neis_base_url=os.getenv("NEIS_BASE_URL", Settings.neis_base_url).strip(),
        neis_timeout_seconds=float(
            os.getenv("NEIS_TIMEOUT_SECONDS", str(Settings.neis_timeout_seconds))
        ),
        mcp_host=os.getenv("MCP_HOST", Settings.mcp_host).strip(),
        mcp_port=int(os.getenv("MCP_PORT", str(Settings.mcp_port))),
        mcp_path=os.getenv("MCP_PATH", Settings.mcp_path).strip(),
    )
