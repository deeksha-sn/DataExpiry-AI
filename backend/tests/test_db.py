import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.data_record import DataRecordModel

TEST_DATABASE_URL = "sqlite:///:memory:"

def test_db_connection_and_tables():
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # Create a test record
        record = DataRecordModel(
            record_id="TEST-001",
            data_type="Test Data",
            category="Customer",
            sensitivity="Low",
            collection_purpose="Testing",
            current_usage="Testing",
            owner="Test Suite",
            created_date="2025-01-01",
            retention_period="1 year",
            expiry_date="2026-01-01",
            status="Active",
            source="Test DB"
        )
        db.add(record)
        db.commit()

        fetched = db.query(DataRecordModel).filter_by(record_id="TEST-001").first()
        assert fetched is not None
        assert fetched.record_id == "TEST-001"
        assert fetched.data_type == "Test Data"
        assert fetched.category == "Customer"
    finally:
        db.close()
