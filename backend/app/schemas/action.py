from typing import Optional
from pydantic import BaseModel, Field, field_validator

ALLOWED_LIFECYCLE_ACTIONS = {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"}

class LifecycleActionRequest(BaseModel):
    action: str = Field(..., json_schema_extra={"example": "DELETE"}, description="Lifecycle action to execute: KEEP, REVIEW, ANONYMIZE, DELETE")
    reason: Optional[str] = Field(None, json_schema_extra={"example": "Mandated retention period exceeded"}, description="Reason or justification for action execution")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ALLOWED_LIFECYCLE_ACTIONS:
            raise ValueError(f"Action must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")
        return upper_v

class LifecycleActionResponse(BaseModel):
    record_id: str = Field(..., description="Unique record code")
    action_executed: str = Field(..., description="Lifecycle action executed: KEEP, REVIEW, ANONYMIZE, DELETE")
    previous_status: Optional[str] = Field(None, description="Previous status of the record")
    new_status: Optional[str] = Field(None, description="New status of the record")
    audit_id: int = Field(..., description="ID of the generated immutable audit record")
    message: str = Field(..., description="Detailed result description")
    deletion_status: Optional[str] = Field(None, description="Updated deletion status")
    anonymization_status: Optional[str] = Field(None, description="Updated anonymization status")
    review_status: Optional[str] = Field(None, description="Updated review status")
