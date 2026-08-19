import logging
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {"PASTE_YOUR_SERVICE_ROLE_KEY_HERE", "", "your-service-role-key"}


class Settings(BaseSettings):
    supabase_url: str
    # Supabase calls this the publishable key in newer projects. Accept the
    # existing ANON_KEY name too so deployments do not need a risky rename.
    supabase_publishable_key: str = Field(
        validation_alias=AliasChoices("SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY")
    )
    supabase_service_role_key: str
    frontend_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def service_role_key_valid(self) -> bool:
        return bool(self.supabase_service_role_key) and self.supabase_service_role_key not in _PLACEHOLDER_KEYS


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_settings() -> None:
    """Log warnings for misconfigured values that will break runtime behaviour."""
    settings = get_settings()

    if not settings.service_role_key_valid:
        logger.error(
            "SUPABASE_SERVICE_ROLE_KEY is missing or still set to a placeholder. "
            "All authenticated data operations (books, pages, photos, orders) will fail "
            "with 401/403 errors. Set a real service-role key in backend/.env. "
            "Find it at: Supabase Dashboard > Settings > API > service_role (secret)."
        )
