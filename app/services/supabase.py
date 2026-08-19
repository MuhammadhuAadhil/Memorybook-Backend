import logging

from supabase import Client, create_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
# This client is used only for validating a bearer token with Supabase Auth.
auth_client: Client = create_client(settings.supabase_url, settings.supabase_publishable_key)
# This client bypasses RLS, so every operation below must first check ownership.
if settings.service_role_key_valid:
    admin_client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
else:
    logger.warning(
        "admin_client created with invalid/placeholder service-role key. "
        "Data operations will fail until a real key is set in backend/.env"
    )
    admin_client: Client = create_client(settings.supabase_url, settings.supabase_publishable_key)
