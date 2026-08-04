from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    request_timeout_seconds: float = 15.0
    browser_timeout_ms: int = 20_000
    max_response_bytes: int = 2_000_000
    user_agent: str = "GeoAuditBot/1.0"

    model_config = SettingsConfigDict(env_prefix="GEO_AUDIT_", env_file=".env")


settings = Settings()
