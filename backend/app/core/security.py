from enum import Enum
from typing import List, Optional
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel

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
    Falls back to user_id='local_dev_user' and role=ADMIN for local dev/testing if headers are omitted.
    """
    user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else "local_dev_user"

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
        role = UserRole.ADMIN

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
