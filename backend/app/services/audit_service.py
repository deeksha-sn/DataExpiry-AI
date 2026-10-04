from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditLogModel

def utc_now():
    return datetime.now(timezone.utc)

class AuditService:
    @staticmethod
    def log_audit_event(
        db: Session,
        record_id: str,
        action: str,
        user: str,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        reason: Optional[str] = None,
        ai_recommendation: Optional[str] = None,
        policy_rule: Optional[str] = None,
        commit: bool = True
    ) -> AuditLogModel:
        """
        Creates an immutable audit log entry.
        Supports atomic participation in outer transactions via commit=False.
        """
        now = utc_now()
        audit_entry = AuditLogModel(
            record_id=record_id.strip(),
            action=action.strip().upper(),
            previous_status=previous_status,
            new_status=new_status,
            user=user.strip(),
            timestamp=now,
            reason=reason,
            ai_recommendation=ai_recommendation,
            policy_rule=policy_rule,
            created_at=now
        )
        db.add(audit_entry)
        if commit:
            db.commit()
            db.refresh(audit_entry)
        else:
            db.flush()
        return audit_entry

    @staticmethod
    def get_audit_logs(
        db: Session,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogModel]:
        """
        Retrieves audit log entries with optional filtering and pagination.
        """
        query = db.query(AuditLogModel)

        if record_id:
            query = query.filter(AuditLogModel.record_id.ilike(f"%{record_id.strip()}%"))
        if action:
            query = query.filter(AuditLogModel.action.ilike(f"%{action.strip()}%"))
        if user:
            query = query.filter(AuditLogModel.user.ilike(f"%{user.strip()}%"))

        return query.order_by(AuditLogModel.audit_id.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_audit_by_id(db: Session, audit_id: int) -> Optional[AuditLogModel]:
        """Retrieves a single audit log entry by its primary key."""
        return db.query(AuditLogModel).filter(AuditLogModel.audit_id == audit_id).first()
