from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import UserRole, CurrentUser, require_role
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

# Roles permitted to read audit logs
AUDIT_READ_ROLES = [
    UserRole.ADMIN,
    UserRole.AUDITOR,
    UserRole.DATA_GOVERNANCE,
    UserRole.PRIVACY_OFFICER,
]

@router.get("", response_model=List[AuditLogResponse])
def get_audit_trail(
    record_id: Optional[str] = Query(None, description="Filter by record ID"),
    action: Optional[str] = Query(None, description="Filter by action (KEEP, REVIEW, ANONYMIZE, DELETE)"),
    user_filter: Optional[str] = Query(None, alias="user", description="Filter by actor user ID"),
    limit: int = Query(100, ge=1, le=500, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Offset index"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(AUDIT_READ_ROLES))
):
    """Retrieve immutable audit log records with optional filtering and pagination."""
    return AuditService.get_audit_logs(
        db=db,
        record_id=record_id,
        action=action,
        user=user_filter,
        limit=limit,
        offset=offset
    )

@router.get("/{record_id}", response_model=List[AuditLogResponse])
def get_audit_trail_for_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(AUDIT_READ_ROLES))
):
    """Retrieve full chronological audit history for a specific data record."""
    return AuditService.get_audit_logs(db=db, record_id=record_id)
