from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.session import Base

def utc_now():
    return datetime.now(timezone.utc)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    record_id = Column(String(50), index=True, nullable=False)
    action = Column(String(50), nullable=False)  # KEEP, REVIEW, ANONYMIZE, DELETE, EVALUATE, STATUS_CHANGE
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    user = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    reason = Column(String(255), nullable=True)
    ai_recommendation = Column(String(50), nullable=True)
    policy_rule = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    @property
    def id(self):
        """Convenience property for generic id lookups."""
        return self.audit_id

    def __repr__(self):
        return f"<AuditLog {self.audit_id} - {self.record_id} [{self.action}] by {self.user}>"
