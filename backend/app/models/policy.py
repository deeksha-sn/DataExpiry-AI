from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from app.database.session import Base

def utc_now():
    return datetime.now(timezone.utc)

class PolicyRuleModel(Base):
    __tablename__ = "retention_policies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), index=True, nullable=False)
    retention_period = Column(String(50), nullable=False)
    retention_days = Column(Integer, nullable=False)
    action_on_expiry = Column(String(20), nullable=False)  # KEEP, REVIEW, ANONYMIZE, DELETE
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<PolicyRule {self.rule_code} - {self.name} ({self.category}: {self.retention_period} -> {self.action_on_expiry})>"
