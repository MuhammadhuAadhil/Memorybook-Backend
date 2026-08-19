import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.supabase import auth_client

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        response = auth_client.auth.get_user(credentials.credentials)
        user = response.user
    except Exception as exc:
        # Never log the bearer token or exception text: either can contain
        # sensitive auth information. The exception type is enough to trace
        # a Render deployment/configuration mismatch in server logs.
        logger.warning("Supabase token validation failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.") from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.")
    return user.id


CurrentUserId = Annotated[str, Depends(current_user_id)]
