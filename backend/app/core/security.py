from enum import Enum
from typing import List, Optional
import logging
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DATA_GOVERNANCE = "DATA_GOVERNANCE"
    PRIVACY_OFFICER = "PRIVACY_OFFICER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"

class CurrentUser(BaseModel):
    user_id: str
    role: UserRole

def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> CurrentUser:
    """
    Extract user identity and role from headers.
    
    SECURITY & LEAST-PRIVILEGE NOTICE:
    - Header-based role assertion is intended strictly for local development and test environments.
    - If headers are absent, identity defaults to 'local_dev_user' with the read-only 'VIEWER' role.
      Unauthenticated requests FAIL CLOSED on privileged policy changes, actions, and audit access.
    - If ALLOW_DEV_HEADER_AUTH is disabled and ENVIRONMENT != 'development', caller-supplied role headers
      are rejected to prevent unauthorized role assumption.
    """
    has_custom_headers = bool((x_user_role and x_user_role.strip()) or (x_user_id and x_user_id.strip()))

    if has_custom_headers:
        allow_dev = (
            getattr(settings, "ALLOW_DEV_HEADER_AUTH", False) is True
            and getattr(settings, "ENVIRONMENT", "") == "development"
        )
        if not allow_dev:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Header-based development identity assertion is disabled outside development environment or without explicit opt-in."
            )

        user_id = x_user_id.strip() if (x_user_id and x_user_id.strip()) else "local_dev_user"
        if x_user_role and x_user_role.strip():
            role_str = x_user_role.strip().upper()
            try:
                role = UserRole(role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid role '{x_user_role}'. Allowed roles: {[r.value for r in UserRole]}"
                )
        else:
            role = UserRole.VIEWER
    else:
        # Default to least-privileged VIEWER role (fails closed on privileged endpoints)
        user_id = "local_dev_user"
        role = UserRole.VIEWER

    return CurrentUser(user_id=user_id, role=role)

def require_role(allowed_roles: List[UserRole]):
    """
    FastAPI dependency factory enforcing that the current user has one of the allowed roles.
    Raises HTTP 403 Forbidden if the user's role is not permitted.
    """
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role.value}' is not authorized. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return dependency
