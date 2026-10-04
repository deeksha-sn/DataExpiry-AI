from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import UserRole, CurrentUser, require_role
from app.services.lifecycle_service import LifecycleService
from app.schemas.action import LifecycleActionRequest, LifecycleActionResponse

router = APIRouter(prefix="/data", tags=["Lifecycle Actions"])

# Roles permitted to call execute-action endpoint
ACTION_PERMITTED_ROLES = [
    UserRole.ADMIN,
    UserRole.DATA_GOVERNANCE,
    UserRole.PRIVACY_OFFICER,
]

@router.post("/{record_id}/execute-action", response_model=LifecycleActionResponse)
def execute_lifecycle_action(
    record_id: str,
    action_in: LifecycleActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(ACTION_PERMITTED_ROLES))
):
    """
    Execute a deterministic lifecycle action on a record.
    Supported actions: KEEP, REVIEW, ANONYMIZE, DELETE (simulated).
    Role permissions are strictly enforced (e.g. PRIVACY_OFFICER cannot execute DELETE).
    An immutable audit record is created atomically within the same transaction.
    """
    try:
        return LifecycleService.execute_action(
            db=db,
            record_id=record_id,
            action=action_in.action,
            user=current_user.user_id,
            role=current_user.role,
            reason=action_in.reason
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
