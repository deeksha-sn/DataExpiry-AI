from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import UserRole, CurrentUser, require_role
from app.models.data_record import DataRecordModel
from app.services.policy_service import PolicyService
from app.services.data_service import DataRecordService
from app.schemas.policy import (
    PolicyRuleCreate,
    PolicyRuleUpdate,
    PolicyRuleResponse,
    PolicyEvaluationItem,
    PolicyEvaluationSummary,
)

router = APIRouter(prefix="/policies", tags=["Retention Policies"])

# Roles permitted to view policies
VIEW_POLICY_ROLES = [
    UserRole.ADMIN,
    UserRole.DATA_GOVERNANCE,
    UserRole.PRIVACY_OFFICER,
    UserRole.AUDITOR,
    UserRole.VIEWER,
]

# Roles permitted to modify policies
MANAGE_POLICY_ROLES = [
    UserRole.ADMIN,
    UserRole.DATA_GOVERNANCE,
]

# Roles permitted to run policy evaluations
EVALUATE_POLICY_ROLES = [
    UserRole.ADMIN,
    UserRole.DATA_GOVERNANCE,
    UserRole.PRIVACY_OFFICER,
    UserRole.AUDITOR,
]

@router.get("", response_model=List[PolicyRuleResponse])
def list_policies(
    active_only: bool = Query(False, description="Filter only active policies"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(VIEW_POLICY_ROLES))
):
    """List all retention policies with optional active-only filter."""
    return PolicyService.list_policies(db=db, active_only=active_only)

@router.post("", response_model=PolicyRuleResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    policy_in: PolicyRuleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(MANAGE_POLICY_ROLES))
):
    """Create a new retention policy."""
    try:
        return PolicyService.create_policy(db=db, policy_in=policy_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{id}", response_model=PolicyRuleResponse)
def get_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(VIEW_POLICY_ROLES))
):
    """Retrieve details of a specific policy by ID."""
    policy = PolicyService.get_policy(db=db, policy_id=id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy rule with ID {id} not found."
        )
    return policy

@router.put("/{id}", response_model=PolicyRuleResponse)
def update_policy(
    id: int,
    policy_in: PolicyRuleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(MANAGE_POLICY_ROLES))
):
    """Update an existing retention policy."""
    try:
        return PolicyService.update_policy(db=db, policy_id=id, policy_in=policy_in)
    except ValueError as e:
        msg = str(e)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=msg)

@router.delete("/{id}", response_model=PolicyRuleResponse)
def deactivate_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(MANAGE_POLICY_ROLES))
):
    """Soft deactivates a retention policy rule (sets is_active=False)."""
    try:
        return PolicyService.deactivate_policy(db=db, policy_id=id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/evaluate", response_model=PolicyEvaluationSummary)
def evaluate_records(
    as_of_date: Optional[str] = Query(None, description="Evaluation baseline date (YYYY-MM-DD), defaults to UTC today"),
    expiring_soon_days: int = Query(30, ge=1, le=365, description="Threshold in days for expiring soon classification"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(EVALUATE_POLICY_ROLES))
):
    """Batch evaluate records against active retention policies."""
    parsed_date = None
    if as_of_date:
        try:
            parsed_date = datetime.strptime(as_of_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format '{as_of_date}'. Expected 'YYYY-MM-DD'."
            )

    return PolicyService.evaluate_all_records(
        db=db,
        as_of_date=parsed_date,
        expiring_soon_days=expiring_soon_days,
        category=category
    )

@router.post("/evaluate/{record_id}", response_model=PolicyEvaluationItem)
def evaluate_single_record(
    record_id: str,
    as_of_date: Optional[str] = Query(None, description="Evaluation baseline date (YYYY-MM-DD), defaults to UTC today"),
    expiring_soon_days: int = Query(30, ge=1, le=365, description="Threshold in days for expiring soon classification"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(EVALUATE_POLICY_ROLES))
):
    """Evaluate a single record against active retention policies."""
    parsed_date = None
    if as_of_date:
        try:
            parsed_date = datetime.strptime(as_of_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format '{as_of_date}'. Expected 'YYYY-MM-DD'."
            )

    record = DataRecordService.get_record_by_identifier(db=db, identifier=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data record '{record_id}' not found."
        )

    return PolicyService.evaluate_record(
        db=db,
        record=record,
        as_of_date=parsed_date,
        expiring_soon_days=expiring_soon_days
    )
