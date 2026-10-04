from typing import Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.data_record import DataRecordModel
from app.services.audit_service import AuditService
from app.schemas.action import LifecycleActionResponse, ALLOWED_LIFECYCLE_ACTIONS
from app.core.security import UserRole

# Define exact action permissions per role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"},
    UserRole.DATA_GOVERNANCE: {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"},
    UserRole.PRIVACY_OFFICER: {"REVIEW", "ANONYMIZE"},
    UserRole.AUDITOR: set(),
    UserRole.VIEWER: set(),
}

class LifecycleService:
    @classmethod
    def execute_action(
        cls,
        db: Session,
        record_id: str,
        action: str,
        user: str,
        role: Union[UserRole, str],
        reason: Optional[str] = None
    ) -> LifecycleActionResponse:
        """
        Executes a deterministic lifecycle action on a data record.
        Enforces role-based permissions and records an immutable audit log atomically.
        Supported actions: KEEP, REVIEW, ANONYMIZE, DELETE (simulated).
        """
        # Validate action
        action_upper = action.strip().upper()
        if action_upper not in ALLOWED_LIFECYCLE_ACTIONS:
            raise ValueError(
                f"Invalid lifecycle action '{action}'. "
                f"Allowed actions: {sorted(ALLOWED_LIFECYCLE_ACTIONS)}"
            )

        # Normalize and validate role
        if isinstance(role, str):
            try:
                user_role = UserRole(role.strip().upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid user role '{role}'."
                )
        else:
            user_role = role

        # Enforce role permissions
        allowed_actions = ROLE_PERMISSIONS.get(user_role, set())
        if action_upper not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{user_role.value}' is not authorized to execute action '{action_upper}'. "
                    f"Allowed actions for this role: {sorted(list(allowed_actions)) or 'None'}"
                )
            )

        # Fetch record
        record = db.query(DataRecordModel).filter(
            DataRecordModel.record_id.ilike(record_id.strip())
        ).first()

        if not record:
            # Check numerical ID fallback
            if record_id.strip().isdigit():
                record = db.query(DataRecordModel).filter(
                    DataRecordModel.id == int(record_id.strip())
                ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data record '{record_id}' not found."
            )

        prev_status = record.status
        new_status = record.status
        message = ""

        try:
            # Execute state transition
            if action_upper == "DELETE":
                # SIMULATED DELETION ONLY:
                # - No SQL DELETE
                # - No row removal
                # - No wiping/clearing of sensitive data columns
                record.deletion_status = "Deleted"
                if record.status != "Expired":
                    record.status = "Expired"
                new_status = record.status
                message = f"Record '{record.record_id}' marked as Deleted (simulated deletion; data preserved for compliance)."

            elif action_upper == "ANONYMIZE":
                record.anonymization_status = "Anonymized"
                record.status = "Archived"
                new_status = "Archived"
                message = f"Record '{record.record_id}' marked as Anonymized and Archived."

            elif action_upper == "REVIEW":
                record.review_status = "In Review"
                new_status = record.status
                message = f"Record '{record.record_id}' queued for human review."

            elif action_upper == "KEEP":
                record.review_status = "Approved"
                new_status = record.status
                message = f"Record '{record.record_id}' approved for continued retention (status: KEEP)."

            # Atomically log audit record in the same transaction
            audit_entry = AuditService.log_audit_event(
                db=db,
                record_id=record.record_id,
                action=action_upper,
                user=user,
                previous_status=prev_status,
                new_status=new_status,
                reason=reason,
                ai_recommendation=record.ai_recommendation,
                policy_rule=record.policy_rule,
                commit=False
            )

            db.commit()
            db.refresh(record)
            db.refresh(audit_entry)

            return LifecycleActionResponse(
                record_id=record.record_id,
                action_executed=action_upper,
                previous_status=prev_status,
                new_status=new_status,
                audit_id=audit_entry.audit_id,
                message=message,
                deletion_status=record.deletion_status,
                anonymization_status=record.anonymization_status,
                review_status=record.review_status
            )

        except Exception as e:
            db.rollback()
            raise e
