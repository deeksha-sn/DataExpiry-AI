import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.audit import AuditLogModel
from app.services.audit_service import AuditService

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

def test_audit_contains_all_required_fields(db_session):
    entry = AuditService.log_audit_event(
        db=db_session,
        record_id="REC-AUDIT-01",
        action="ANONYMIZE",
        user="test_auditor",
        previous_status="Active",
        new_status="Archived",
        reason="Compliance policy enforcement",
        ai_recommendation="ANONYMIZE",
        policy_rule="POL-CUS-01"
    )

    # Validate all minimum required fields
    assert entry.audit_id is not None
    assert entry.record_id == "REC-AUDIT-01"
    assert entry.action == "ANONYMIZE"
    assert entry.previous_status == "Active"
    assert entry.new_status == "Archived"
    assert entry.user == "test_auditor"
    assert entry.timestamp is not None
    assert entry.reason == "Compliance policy enforcement"
    assert entry.ai_recommendation == "ANONYMIZE"
    assert entry.policy_rule == "POL-CUS-01"
    assert entry.created_at is not None

def test_audit_filtering_by_record_id(db_session):
    AuditService.log_audit_event(db=db_session, record_id="REC-AAA", action="KEEP", user="user1")
    AuditService.log_audit_event(db=db_session, record_id="REC-BBB", action="REVIEW", user="user2")
    AuditService.log_audit_event(db=db_session, record_id="REC-AAA", action="DELETE", user="user3")

    logs_aaa = AuditService.get_audit_logs(db=db_session, record_id="REC-AAA")
    assert len(logs_aaa) == 2
    for log in logs_aaa:
        assert log.record_id == "REC-AAA"

    logs_bbb = AuditService.get_audit_logs(db=db_session, record_id="REC-BBB")
    assert len(logs_bbb) == 1
    assert logs_bbb[0].record_id == "REC-BBB"

def test_audit_filtering_by_action(db_session):
    AuditService.log_audit_event(db=db_session, record_id="REC-1", action="DELETE", user="admin")
    AuditService.log_audit_event(db=db_session, record_id="REC-2", action="KEEP", user="admin")
    AuditService.log_audit_event(db=db_session, record_id="REC-3", action="DELETE", user="admin")

    delete_logs = AuditService.get_audit_logs(db=db_session, action="DELETE")
    assert len(delete_logs) == 2
    for log in delete_logs:
        assert log.action == "DELETE"

    keep_logs = AuditService.get_audit_logs(db=db_session, action="KEEP")
    assert len(keep_logs) == 1
    assert keep_logs[0].action == "KEEP"
