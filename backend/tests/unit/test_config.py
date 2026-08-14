from pathlib import Path

from app.config import get_settings


def test_settings_loads_neis_env_file(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "NEIS_API_KEY=test-key",
                "NEIS_BASE_URL=https://example.test/hub",
                "NEIS_TIMEOUT_SECONDS=7",
                "BACKEND_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4173",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("NEIS_API_KEY", raising=False)
    monkeypatch.delenv("NEIS_BASE_URL", raising=False)
    monkeypatch.delenv("NEIS_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("BACKEND_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv("NEIS_ENV_FILE", str(env_file))

    settings = get_settings()

    assert settings.neis_api_key == "test-key"
    assert settings.neis_base_url == "https://example.test/hub"
    assert settings.neis_timeout_seconds == 7
    assert settings.allowed_origins == ["http://localhost:5173", "http://localhost:4173"]


def test_default_origins_allow_localhost_and_loopback(monkeypatch) -> None:
    monkeypatch.delenv("NEIS_ENV_FILE", raising=False)
    monkeypatch.delenv("BACKEND_ALLOWED_ORIGINS", raising=False)

    settings = get_settings()

    assert "http://localhost:5173" in settings.allowed_origins
    assert "http://127.0.0.1:5173" in settings.allowed_origins
