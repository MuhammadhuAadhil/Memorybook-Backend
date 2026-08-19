from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Unauthenticated liveness endpoint for local and deployment probes."""
    return {"status": "ok"}


@router.get("/health/config")
def health_config() -> dict[str, object]:
    """Report whether critical configuration values are set (without leaking secrets)."""
    settings = get_settings()
    return {
        "status": "ok",
        "supabase_url_configured": bool(settings.supabase_url),
        "publishable_key_configured": bool(settings.supabase_publishable_key),
        "service_role_key_configured": settings.service_role_key_valid,
        "cors_origins": settings.cors_origins,
    }
