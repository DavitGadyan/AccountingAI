"""Application configuration.

Everything that differs between a laptop, CI and production lives here and nowhere else.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AAI_", extra="ignore")

    environment: str = "development"
    debug: bool = True

    # --- Database -----------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://accountingai:accountingai@localhost:5432/accountingai"
    db_echo: bool = False

    # --- Auth ---------------------------------------------------------------------
    secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 8

    # --- Object storage (documents are never stored in the database) ---------------
    s3_endpoint: str | None = "http://localhost:9000"
    s3_bucket: str = "accountingai-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"

    # --- Queue --------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # --- Extraction ---------------------------------------------------------------
    anthropic_api_key: str | None = None
    extraction_model: str = "claude-sonnet-5"
    memo_model: str = "claude-opus-5"
    # Below this confidence an extracted field is always routed to a human. Tuned so that
    # the review queue stays short without letting a wrong number reach a return.
    extraction_confidence_threshold: float = 0.90

    # --- E-file -------------------------------------------------------------------
    # The platform is not an IRS-authorized transmitter; it integrates with one.
    efile_provider: str = "stub"
    efile_base_url: str | None = None
    efile_api_key: str | None = None
    efile_etin: str | None = None

    # --- Tie-out ------------------------------------------------------------------
    # A year-over-year swing larger than either bound is flagged for reviewer attention.
    variance_absolute_threshold: float = 5_000.0
    variance_relative_threshold: float = 0.25


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
