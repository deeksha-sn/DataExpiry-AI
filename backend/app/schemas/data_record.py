from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class DataRecordBase(BaseModel):
    record_id: str = Field(..., json_schema_extra={"example": "CUS-1001"}, description="Unique record code")
    data_type: str = Field(..., json_schema_extra={"example": "Customer Profile"}, description="Specific data type")
    category: str = Field(..., json_schema_extra={"example": "Customer"}, description="Broad classification category")
    sensitivity: str = Field(..., json_schema_extra={"example": "High"}, description="Sensitivity level: High, Medium, Low")
    collection_purpose: str = Field(..., json_schema_extra={"example": "Order Processing"}, description="Original purpose of collection")
    current_usage: str = Field(..., json_schema_extra={"example": "Order Processing"}, description="Current usage of data")
    owner: str = Field(..., json_schema_extra={"example": "Customer Success Dept"}, description="Responsible department or team")
    created_date: str = Field(..., json_schema_extra={"example": "2025-01-15"}, description="Original creation date (YYYY-MM-DD)")
    retention_period: str = Field(..., json_schema_extra={"example": "2 years"}, description="Mandated retention period")
    expiry_date: str = Field(..., json_schema_extra={"example": "2027-01-15"}, description="Mandated expiry date (YYYY-MM-DD)")
    status: str = Field(..., json_schema_extra={"example": "Active"}, description="Status: Active, Expired, Expiring Soon")
    last_accessed: Optional[str] = Field(None, json_schema_extra={"example": "2025-02-10"}, description="Date of last access")
    source: str = Field(..., json_schema_extra={"example": "CRM Database"}, description="Source system or database")

    # Optional Future Extension Fields
    purpose_mismatch: Optional[bool] = Field(False, description="Flag indicating usage diverges from purpose")
    risk_level: Optional[str] = Field("Low", description="Risk rating: Low, Medium, High, Critical")
    ai_recommendation: Optional[str] = Field("KEEP", description="Action recommendation: KEEP, REVIEW, ANONYMIZE, DELETE")
    ai_explanation: Optional[str] = Field(None, description="Detailed explanation for recommendation")
    policy_rule: Optional[str] = Field(None, description="Applied policy rule identifier")
    review_status: Optional[str] = Field("Pending", description="Human review status")
    anonymization_status: Optional[str] = Field("Not Required", description="Anonymization pipeline status")
    deletion_status: Optional[str] = Field("Not Required", description="Deletion pipeline status")

class DataRecordCreate(DataRecordBase):
    pass

class DataRecordUpdate(BaseModel):
    data_type: Optional[str] = None
    category: Optional[str] = None
    sensitivity: Optional[str] = None
    collection_purpose: Optional[str] = None
    current_usage: Optional[str] = None
    owner: Optional[str] = None
    retention_period: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = None
    last_accessed: Optional[str] = None
    source: Optional[str] = None
    purpose_mismatch: Optional[bool] = None
    risk_level: Optional[str] = None
    ai_recommendation: Optional[str] = None
    ai_explanation: Optional[str] = None
    policy_rule: Optional[str] = None
    review_status: Optional[str] = None
    anonymization_status: Optional[str] = None
    deletion_status: Optional[str] = None

class DataRecordResponse(DataRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    service: str = Field(..., json_schema_extra={"example": "DATAEXPIRY API"})
    version: Optional[str] = Field(None, json_schema_extra={"example": "1.0.0"})

class PurposeMismatchCheckRequest(BaseModel):
    collection_purpose: str = Field(..., min_length=1, json_schema_extra={"example": "Order Processing & Delivery"})
    current_usage: str = Field(..., min_length=1, json_schema_extra={"example": "Targeted Marketing Campaigns"})
    category: Optional[str] = Field("Customer", json_schema_extra={"example": "Customer"})
    sensitivity: Optional[str] = Field("Medium", json_schema_extra={"example": "High"})
    status: Optional[str] = Field("Active", json_schema_extra={"example": "Active"})
    expiry_date: Optional[str] = Field("2026-12-31", json_schema_extra={"example": "2026-12-31"})

class PurposeMismatchResult(BaseModel):
    record_id: Optional[str] = None
    category: str
    sensitivity: str
    collection_purpose: str
    current_usage: str
    purpose_mismatch: bool
    risk_level: str
    ai_recommendation: str
    explanation: str
    analysis_mode: str

class BatchAIAnalysisResponse(BaseModel):
    total_analyzed: int
    potential_mismatches: int
    records_requiring_review: int
    recommendations: Dict[str, int]
    risk_breakdown: Dict[str, int]
    records: List[PurposeMismatchResult]
