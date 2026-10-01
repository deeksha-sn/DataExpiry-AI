from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.data_record import DataRecordModel
from app.schemas.data_record import DataRecordCreate

class DataRecordService:
    @staticmethod
    def get_records(
        db: Session,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sensitivity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DataRecordModel]:
        """Fetch data records with optional filtering."""
        query = db.query(DataRecordModel)
        if category:
            query = query.filter(DataRecordModel.category.ilike(f"%{category}%"))
        if status:
            query = query.filter(DataRecordModel.status.ilike(f"%{status}%"))
        if sensitivity:
            query = query.filter(DataRecordModel.sensitivity.ilike(f"%{sensitivity}%"))
        
        return query.order_by(DataRecordModel.id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_record_by_identifier(db: Session, identifier: str) -> Optional[DataRecordModel]:
        """Fetch a single record by record_id (e.g. CUS-1001) or numerical id."""
        if identifier.isdigit():
            rec = db.query(DataRecordModel).filter(DataRecordModel.id == int(identifier)).first()
            if rec:
                return rec

        return db.query(DataRecordModel).filter(DataRecordModel.record_id.ilike(identifier)).first()

    @staticmethod
    def create_record(db: Session, record_in: DataRecordCreate) -> DataRecordModel:
        """Create a new data record in the database."""
        # Check if record_id already exists
        existing = db.query(DataRecordModel).filter(
            DataRecordModel.record_id.ilike(record_in.record_id)
        ).first()
        if existing:
            raise ValueError(f"Record with record_id '{record_in.record_id}' already exists.")

        db_obj = DataRecordModel(**record_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def count_records(db: Session) -> int:
        """Get total count of records."""
        return db.query(DataRecordModel).count()
