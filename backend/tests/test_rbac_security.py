import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.data_record import DataRecordModel
from app.core.security import (
    UserRole,
    CurrentUser,
    get_current_user,
    require_role,
)
from app.services.lifecycle_service import LifecycleService

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
def test_record(db_session):
    record = DataRecordModel(
        record_id="RBAC-REC-1",
        data_type="Customer Profile",
        category="Customer",
        sensitivity="High",
        collection_purpose="Account Ops",
        current_usage="Account Ops",
        owner="Customer Care",
        created_date="2023-01-01",
        retention_period="2 years",
        expiry_date="2025-01-01",
        status="Active",
        source="CRM"
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record

# ---------------------------------------------------------------------------
# Header Extraction & Dependency Tests
# ---------------------------------------------------------------------------

def test_fallback_dev_user_when_headers_absent():
    user = get_current_user(x_user_id=None, x_user_role=None)
    assert user.user_id == "local_dev_user"
    assert user.role == UserRole.ADMIN

def test_custom_user_and_role_headers():
    user = get_current_user(x_user_id="officer_42", x_user_role="PRIVACY_OFFICER")
    assert user.user_id == "officer_42"
    assert user.role == UserRole.PRIVACY_OFFICER

def test_invalid_role_header_rejected():
    with pytest.raises(HTTPException) as exc:
        get_current_user(x_user_id="user1", x_user_role="SUPER_HACKER")
    assert exc.value.status_code == 403

def test_require_role_dependency_factory():
    policy_management_guard = require_role([UserRole.ADMIN, UserRole.DATA_GOVERNANCE])

    # Admin passes
    admin_user = CurrentUser(user_id="admin_1", role=UserRole.ADMIN)
    assert policy_management_guard(admin_user) == admin_user

    # Data Governance passes
    dg_user = CurrentUser(user_id="dg_1", role=UserRole.DATA_GOVERNANCE)
    assert policy_management_guard(dg_user) == dg_user

    # Auditor blocked with 403
    auditor = CurrentUser(user_id="audit_1", role=UserRole.AUDITOR)
    with pytest.raises(HTTPException) as exc1:
        policy_management_guard(auditor)
    assert exc1.value.status_code == 403

    # Viewer blocked with 403
    viewer = CurrentUser(user_id="view_1", role=UserRole.VIEWER)
    with pytest.raises(HTTPException) as exc2:
        policy_management_guard(viewer)
    assert exc2.value.status_code == 403

# ---------------------------------------------------------------------------
# Lifecycle Action Permissions by Role (Requirements 24 - 33)
# ---------------------------------------------------------------------------

def test_admin_can_perform_all_actions(db_session, test_record):
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        resp = LifecycleService.execute_action(
            db=db_session,
            record_id=test_record.record_id,
            action=action,
            user="admin_user",
            role=UserRole.ADMIN
        )
        assert resp.action_executed == action

def test_data_governance_can_execute_actions(db_session, test_record):
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        resp = LifecycleService.execute_action(
            db=db_session,
            record_id=test_record.record_id,
            action=action,
            user="steward_user",
            role=UserRole.DATA_GOVERNANCE
        )
        assert resp.action_executed == action

def test_privacy_officer_can_review(db_session, test_record):
    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=test_record.record_id,
        action="REVIEW",
        user="po_user",
        role=UserRole.PRIVACY_OFFICER
    )
    assert resp.action_executed == "REVIEW"

def test_privacy_officer_can_anonymize(db_session, test_record):
    resp = LifecycleService.execute_action(
        db=db_session,
        record_id=test_record.record_id,
        action="ANONYMIZE",
        user="po_user",
        role=UserRole.PRIVACY_OFFICER
    )
    assert resp.action_executed == "ANONYMIZE"

def test_privacy_officer_cannot_delete(db_session, test_record):
    with pytest.raises(HTTPException) as exc:
        LifecycleService.execute_action(
            db=db_session,
            record_id=test_record.record_id,
            action="DELETE",
            user="po_user",
            role=UserRole.PRIVACY_OFFICER
        )
    assert exc.value.status_code == 403

def test_auditor_cannot_execute_lifecycle_actions(db_session, test_record):
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        with pytest.raises(HTTPException) as exc:
            LifecycleService.execute_action(
                db=db_session,
                record_id=test_record.record_id,
                action=action,
                user="auditor_user",
                role=UserRole.AUDITOR
            )
        assert exc.value.status_code == 403

def test_viewer_cannot_execute_lifecycle_actions(db_session, test_record):
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        with pytest.raises(HTTPException) as exc:
            LifecycleService.execute_action(
                db=db_session,
                record_id=test_record.record_id,
                action=action,
                user="viewer_user",
                role=UserRole.VIEWER
            )
        assert exc.value.status_code == 403
