from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.data_record import (
    DataRecordCreate,
    DataRecordResponse,
    HealthResponse,
)
from app.services.data_service import DataRecordService
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
