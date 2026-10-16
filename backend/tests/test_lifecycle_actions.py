import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.data_record import DataRecordModel
from app.models.audit import AuditLogModel
from app.services.lifecycle_service import LifecycleService
from app.core.security import UserRole

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_record(db_session):
    record = DataRecordModel(
        record_id="CUS-LIFECYCLE-1",
        data_type="Customer Profile",
        category="Customer",
        sensitivity="High",
        collection_purpose="Order Fulfillment",
        current_usage="Order Fulfillment",
        owner="Customer Operations",
        created_date="2023-01-01",
        retention_period="2 years",
        expiry_date="2025-01-01",
        status="Active",
        source="CRM Database",
        purpose_mismatch=False,
        review_status="Pending",
        anonymization_status="Not Required",
        deletion_status="Not Required"
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record

def test_keep_action_updates_review_status(db_session, sample_record):
    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=sample_record.record_id,
        action="KEEP",
        user="test_admin",
        role=UserRole.ADMIN,
        reason="Approved retention continuation"
    )
    assert resp.action_executed == "KEEP"
    assert resp.review_status == "Approved"

    refreshed = db_session.query(DataRecordModel).filter_by(record_id=sample_record.record_id).first()
    assert refreshed.review_status == "Approved"

    # Verifies audit log created
    audit = db_session.query(AuditLogModel).filter_by(audit_id=resp.audit_id).first()
    assert audit is not None
    assert audit.action == "KEEP"
    assert audit.user == "test_admin"

def test_review_action_updates_review_status(db_session, sample_record):
    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=sample_record.record_id,
        action="REVIEW",
        user="privacy_officer_1",
        role=UserRole.PRIVACY_OFFICER,
        reason="Flagged for manual inspection"
    )
    assert resp.action_executed == "REVIEW"
    assert resp.review_status == "In Review"

    refreshed = db_session.query(DataRecordModel).filter_by(record_id=sample_record.record_id).first()
    assert refreshed.review_status == "In Review"

    # Verifies audit log created
    audit = db_session.query(AuditLogModel).filter_by(audit_id=resp.audit_id).first()
    assert audit is not None
    assert audit.action == "REVIEW"

def test_anonymize_action_updates_anonymization_status(db_session, sample_record):
    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=sample_record.record_id,
        action="ANONYMIZE",
        user="steward_1",
        role=UserRole.DATA_GOVERNANCE,
        reason="Retention deadline passed"
    )
    assert resp.action_executed == "ANONYMIZE"
    assert resp.anonymization_status == "Anonymized"
    assert resp.new_status == "Archived"

    refreshed = db_session.query(DataRecordModel).filter_by(record_id=sample_record.record_id).first()
    assert refreshed.anonymization_status == "Anonymized"
    assert refreshed.status == "Archived"

    # Verifies audit log created
    audit = db_session.query(AuditLogModel).filter_by(audit_id=resp.audit_id).first()
    assert audit is not None
    assert audit.action == "ANONYMIZE"
    assert audit.new_status == "Archived"

def test_delete_action_is_simulated_only(db_session, sample_record):
    # Verify pre-conditions: row exists with sensitive data
    orig_owner = sample_record.owner
    orig_purpose = sample_record.collection_purpose

    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=sample_record.record_id,
        action="DELETE",
        user="admin_user",
        role=UserRole.ADMIN,
        reason="Mandated deletion simulation"
    )
    assert resp.action_executed == "DELETE"
    assert resp.deletion_status == "Deleted"

    # 1. Assert row still physically exists in database
    record_in_db = db_session.query(DataRecordModel).filter_by(record_id=sample_record.record_id).first()
    assert record_in_db is not None

    # 2. Assert sensitive fields are NOT cleared
    assert record_in_db.owner == orig_owner
    assert record_in_db.collection_purpose == orig_purpose
    assert record_in_db.data_type == "Customer Profile"
    assert record_in_db.deletion_status == "Deleted"

    # 3. Assert audit record was generated
    audit = db_session.query(AuditLogModel).filter_by(audit_id=resp.audit_id).first()
    assert audit is not None
    assert audit.action == "DELETE"
    assert audit.record_id == sample_record.record_id
    assert audit.user == "admin_user"
