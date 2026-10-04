from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_LIFECYCLE_ACTIONS = {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"}
ALLOWED_EXPIRY_STATUSES = {"ACTIVE", "EXPIRING_SOON", "EXPIRED"}

class PolicyRuleBase(BaseModel):
    rule_code: str = Field(..., json_schema_extra={"example": "POL-CUS-01"}, description="Unique policy rule code")
    name: str = Field(..., json_schema_extra={"example": "Customer Data Retention Policy"}, description="Descriptive policy name")
    category: str = Field(..., json_schema_extra={"example": "Customer"}, description="Data category this policy governs")
    retention_period: str = Field(..., json_schema_extra={"example": "2 years"}, description="Retention duration description")
    retention_days: int = Field(..., ge=1, json_schema_extra={"example": 730}, description="Retention duration converted to days")
    action_on_expiry: str = Field(..., json_schema_extra={"example": "REVIEW"}, description="Action to take on expiry: KEEP, REVIEW, ANONYMIZE, DELETE")
    description: Optional[str] = Field(None, json_schema_extra={"example": "Demonstration retention rule for customer records"}, description="Detailed rule description")
    is_active: bool = Field(True, description="Whether this policy rule is active")

    @field_validator("action_on_expiry")
    @classmethod
    def validate_action(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ALLOWED_LIFECYCLE_ACTIONS:
            raise ValueError(f"action_on_expiry must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")
        return upper_v

class PolicyRuleCreate(PolicyRuleBase):
    pass

class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    retention_period: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=1)
    action_on_expiry: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("action_on_expiry")
    @classmethod
    def validate_action(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            upper_v = v.strip().upper()
            if upper_v not in ALLOWED_LIFECYCLE_ACTIONS:
                raise ValueError(f"action_on_expiry must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")
            return upper_v
        return v

class PolicyRuleResponse(PolicyRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PolicyEvaluationItem(BaseModel):
    record_id: str = Field(..., description="Unique record identifier")
    category: str = Field(..., description="Record classification category")
    expiry_date: str = Field(..., description="Expiry date string (YYYY-MM-DD)")
    expiry_status: str = Field(..., description="Expiry status: ACTIVE, EXPIRING_SOON, EXPIRED")
    days_until_expiry: int = Field(..., description="Days remaining until expiry (negative if expired)")
    deterministic_recommendation: str = Field(..., description="Final deterministic outcome: KEEP, REVIEW, ANONYMIZE, DELETE")
    matched_policy_rule: Optional[str] = Field(None, description="Rule code that governed the decision")
    ai_recommendation: Optional[str] = Field(None, description="Input AI recommendation considered")
    purpose_mismatch: bool = Field(False, description="Whether usage diverges from purpose")
    evaluation_reason: str = Field(..., description="Reasoning narrative for deterministic decision")

    @field_validator("expiry_status")
    @classmethod
    def validate_expiry_status(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ALLOWED_EXPIRY_STATUSES:
            raise ValueError(f"expiry_status must be one of {sorted(ALLOWED_EXPIRY_STATUSES)}")
        return upper_v

    @field_validator("deterministic_recommendation")
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        upper_v = v.strip().upper()
        if upper_v not in ALLOWED_LIFECYCLE_ACTIONS:
            raise ValueError(f"deterministic_recommendation must be one of {sorted(ALLOWED_LIFECYCLE_ACTIONS)}")
        return upper_v

    model_config = ConfigDict(from_attributes=True)

class PolicyEvaluationSummary(BaseModel):
    total_evaluated: int = Field(..., description="Total number of evaluated records")
    active_count: int = Field(..., description="Records currently active")
    expiring_soon_count: int = Field(..., description="Records expiring within threshold")
    expired_count: int = Field(..., description="Records past expiry date")
    recommendations: Dict[str, int] = Field(..., description="Counts per lifecycle recommendation")
    as_of_date: str = Field(..., description="Date used for evaluation baseline (YYYY-MM-DD)")
    expiring_soon_days: int = Field(..., description="Configurable threshold in days for expiring soon")
    records: List[PolicyEvaluationItem] = Field(default_factory=list, description="Detailed record evaluations")
