from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.data_record import (
    DataRecordCreate,
    DataRecordResponse,
    HealthResponse,
    PurposeMismatchCheckRequest,
    PurposeMismatchResult,
    BatchAIAnalysisResponse,
)
from app.services.data_service import DataRecordService
from app.services.ai_service import AIService
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION
    )

@router.get("/data", response_model=List[DataRecordResponse], tags=["Data Records"])
def get_all_records(
    category: Optional[str] = Query(None, description="Filter by data category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Active, Expired, Expiring Soon)"),
    sensitivity: Optional[str] = Query(None, description="Filter by sensitivity (High, Medium, Low)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve all enterprise data records with optional query filtering."""
    records = DataRecordService.get_records(
        db=db,
        category=category,
        status=status_filter,
        sensitivity=sensitivity,
        limit=limit,
        offset=offset
    )
    return records

@router.get("/data/{record_id}", response_model=DataRecordResponse, tags=["Data Records"])
def get_single_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve a specific data record by record_id (e.g. CUS-1001) or internal ID."""
    record = DataRecordService.get_record_by_identifier(db=db, identifier=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data record '{record_id}' not found."
        )
    return record

@router.post("/data", response_model=DataRecordResponse, status_code=status.HTTP_201_CREATED, tags=["Data Records"])
def create_new_record(
    record_in: DataRecordCreate,
    db: Session = Depends(get_db)
):
    """Create a new enterprise data record."""
    try:
        new_record = DataRecordService.create_record(db=db, record_in=record_in)
        return new_record
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ==============================================================================
# AI & Purpose Governance Endpoints (Assigned to Team Member 2)
# ==============================================================================

@router.post("/ai/batch-analyze", response_model=BatchAIAnalysisResponse, tags=["AI Governance"])
def run_batch_ai_analysis(
    db: Session = Depends(get_db)
):
    """
    Executes automated purpose mismatch detection and lifecycle recommendations
    across all stored data records, updating their risk levels and explanations.
    """
    results = AIService.batch_analyze_database(db=db, persist_results=True)
    return results

@router.post("/data/{record_id}/analyze", response_model=PurposeMismatchResult, tags=["AI Governance"])
def analyze_single_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """
    Executes AI analysis for a specific record by ID and updates its record in the database.
    """
    record = DataRecordService.get_record_by_identifier(db=db, identifier=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data record '{record_id}' not found."
        )

    analysis = AIService.analyze_record({
        "record_id": record.record_id,
        "category": record.category,
        "sensitivity": record.sensitivity,
        "collection_purpose": record.collection_purpose,
        "current_usage": record.current_usage,
        "status": record.status,
        "expiry_date": record.expiry_date,
    })

    # Persist updated analysis
    setattr(record, "purpose_mismatch", analysis["purpose_mismatch"])
    setattr(record, "risk_level", analysis["risk_level"])
    setattr(record, "ai_recommendation", analysis["ai_recommendation"])
    setattr(record, "ai_explanation", analysis["explanation"])
    db.commit()
    db.refresh(record)

    return PurposeMismatchResult(**analysis)

@router.post("/ai/check-mismatch", response_model=PurposeMismatchResult, tags=["AI Governance"])
def check_purpose_mismatch_playground(
    request: PurposeMismatchCheckRequest
):
    """
    Interactive playground endpoint for evaluating purpose-usage compatibility
    and lifecycle recommendations without altering database records.
    """
    analysis = AIService.analyze_record({
        "record_id": "PLAYGROUND-TEST",
        "category": request.category or "General",
        "sensitivity": request.sensitivity or "Medium",
        "collection_purpose": request.collection_purpose,
        "current_usage": request.current_usage,
        "status": request.status or "Active",
        "expiry_date": request.expiry_date or "2026-12-31",
    })
    return PurposeMismatchResult(**analysis)

@router.get("/ai/summary", tags=["AI Governance"])
def get_ai_governance_summary(
    db: Session = Depends(get_db)
):
    """
    Returns high-level statistics regarding purpose mismatch drift,
    risk distribution, and recommendation counts.
    """
    from app.models.data_record import DataRecordModel
    records = db.query(DataRecordModel).all()
    total = len(records)
    mismatches = sum(1 for r in records if bool(getattr(r, "purpose_mismatch", False)))
    reviews = sum(1 for r in records if (getattr(r, "ai_recommendation", "") == "REVIEW" or getattr(r, "status", "") == "Expiring Soon"))
    high_sensitivity = sum(1 for r in records if getattr(r, "sensitivity", "") == "High")
    rec_counts = {
        "KEEP": sum(1 for r in records if getattr(r, "ai_recommendation", "") == "KEEP"),
        "REVIEW": sum(1 for r in records if getattr(r, "ai_recommendation", "") == "REVIEW"),
        "ANONYMIZE": sum(1 for r in records if getattr(r, "ai_recommendation", "") == "ANONYMIZE"),
        "DELETE": sum(1 for r in records if getattr(r, "ai_recommendation", "") == "DELETE"),
    }
    risk_counts = {
        "Critical": sum(1 for r in records if getattr(r, "risk_level", "") == "Critical"),
        "High": sum(1 for r in records if getattr(r, "risk_level", "") == "High"),
        "Medium": sum(1 for r in records if getattr(r, "risk_level", "") == "Medium"),
        "Low": sum(1 for r in records if getattr(r, "risk_level", "") == "Low"),
    }

    category_counts = {}
    for r in records:
        cat = str(getattr(r, "category", "General"))
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "total_records": total,
        "potential_mismatches": mismatches,
        "records_requiring_review": reviews,
        "high_sensitivity_count": high_sensitivity,
        "recommendations": rec_counts,
        "risk_breakdown": risk_counts,
        "category_breakdown": category_counts,
    }
