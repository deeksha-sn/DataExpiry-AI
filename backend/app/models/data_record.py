from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from app.database.session import Base

def utc_now():
    return datetime.now(timezone.utc)

class DataRecordModel(Base):
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    record_id = Column(String(50), unique=True, index=True, nullable=False)
    data_type = Column(String(100), nullable=False)
    category = Column(String(50), index=True, nullable=False)
    sensitivity = Column(String(20), nullable=False)
    collection_purpose = Column(String(255), nullable=False)
    current_usage = Column(String(255), nullable=False)
    owner = Column(String(100), nullable=False)
    created_date = Column(String(20), nullable=False)
    retention_period = Column(String(50), nullable=False)
    expiry_date = Column(String(20), index=True, nullable=False)
    status = Column(String(30), index=True, nullable=False)
    last_accessed = Column(String(20), nullable=True)
    source = Column(String(100), nullable=False)

    # Future-compatible extension fields (for Team Members 2 & 4)
    purpose_mismatch = Column(Boolean, default=False, nullable=True)
    risk_level = Column(String(20), default="Low", nullable=True)
    ai_recommendation = Column(String(20), default="KEEP", nullable=True)
    ai_explanation = Column(Text, nullable=True)
    policy_rule = Column(String(100), nullable=True)
    review_status = Column(String(30), default="Pending", nullable=True)
    anonymization_status = Column(String(30), default="Not Required", nullable=True)
    deletion_status = Column(String(30), default="Not Required", nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<DataRecord {self.record_id} - {self.data_type} ({self.status})>"
