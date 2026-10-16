from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AuditLogBase(BaseModel):
    record_id: str = Field(..., description="Unique record identifier affected")
    action: str = Field(..., description="Lifecycle action executed: KEEP, REVIEW, ANONYMIZE, DELETE, etc.")
    previous_status: Optional[str] = Field(None, description="Status prior to action execution")
    new_status: Optional[str] = Field(None, description="Status after action execution")
    user: str = Field(..., description="User or role who triggered the action")
    reason: Optional[str] = Field(None, description="Justification or policy narrative for the action")
    ai_recommendation: Optional[str] = Field(None, description="AI recommendation state at time of event")
    policy_rule: Optional[str] = Field(None, description="Policy rule governing the action")

class AuditLogCreate(AuditLogBase):
    timestamp: Optional[datetime] = None

class AuditLogResponse(AuditLogBase):
    audit_id: int = Field(..., description="Unique primary key of the audit log entry")
    timestamp: datetime = Field(..., description="Event occurrence timestamp")
    created_at: datetime = Field(..., description="Audit record persistence timestamp")

    model_config = ConfigDict(from_attributes=True)

class AuditFilterParams(BaseModel):
    record_id: Optional[str] = None
    action: Optional[str] = None
    user: Optional[str] = None
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)
