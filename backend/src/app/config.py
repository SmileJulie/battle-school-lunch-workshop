import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    neis_api_key: str | None
    neis_base_url: str
    neis_timeout_seconds: float
    allowed_origins: list[str]


def get_settings() -> Settings:
    load_env_files()
    raw_origins = os.getenv("BACKEND_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return Settings(
        neis_api_key=os.getenv("NEIS_API_KEY"),
        neis_base_url=os.getenv("NEIS_BASE_URL", "https://open.neis.go.kr/hub").rstrip("/"),
        neis_timeout_seconds=float(os.getenv("NEIS_TIMEOUT_SECONDS", "5")),
        allowed_origins=allowed_origins,
    )


def load_env_files() -> None:
    backend_env_file = Path(__file__).resolve().parents[2] / ".env"
    env_files = [
        Path(value) if (value := os.getenv("NEIS_ENV_FILE")) else None,
        backend_env_file,
    ]
    for env_file in env_files:
        if env_file and env_file.exists():
            load_dotenv(env_file, override=False)
