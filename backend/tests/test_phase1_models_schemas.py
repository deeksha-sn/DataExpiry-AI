import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.policy import PolicyRuleModel
from app.models.audit import AuditLogModel
from app.schemas.policy import (
    PolicyRuleCreate,
    PolicyRuleResponse,
    PolicyEvaluationItem,
    PolicyEvaluationSummary,
)
from app.schemas.audit import AuditLogResponse
from app.schemas.action import LifecycleActionRequest, LifecycleActionResponse

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

def test_policy_rule_model_crud(db_session):
    policy = PolicyRuleModel(
        rule_code="POL-TEST-01",
        name="Test Customer Retention",
        category="Customer",
        retention_period="2 years",
        retention_days=730,
        action_on_expiry="REVIEW",
        description="Demo customer retention policy",
        is_active=True
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)

    assert policy.id is not None
    assert policy.rule_code == "POL-TEST-01"
    assert policy.action_on_expiry == "REVIEW"
    assert policy.retention_days == 730
    assert policy.created_at is not None
    assert "POL-TEST-01" in repr(policy)

def test_audit_log_model_fields(db_session):
    audit_entry = AuditLogModel(
        record_id="CUS-1001",
        action="ANONYMIZE",
        previous_status="Active",
        new_status="Archived",
        user="test_admin",
        reason="Exceeded retention policy",
        ai_recommendation="ANONYMIZE",
        policy_rule="POL-CUS-01"
    )
    db_session.add(audit_entry)
    db_session.commit()
    db_session.refresh(audit_entry)

    # Validate all minimum required fields are present and correctly populated
    assert audit_entry.audit_id is not None
    assert audit_entry.id == audit_entry.audit_id
    assert audit_entry.record_id == "CUS-1001"
    assert audit_entry.action == "ANONYMIZE"
    assert audit_entry.previous_status == "Active"
    assert audit_entry.new_status == "Archived"
    assert audit_entry.user == "test_admin"
    assert audit_entry.timestamp is not None
    assert audit_entry.reason == "Exceeded retention policy"
    assert audit_entry.ai_recommendation == "ANONYMIZE"
    assert audit_entry.policy_rule == "POL-CUS-01"
    assert audit_entry.created_at is not None
    assert "CUS-1001" in repr(audit_entry)

def test_policy_schema_validation():
    # Valid policy create
    valid_data = {
        "rule_code": "POL-TXN-01",
        "name": "Transaction Policy",
        "category": "Transaction",
        "retention_period": "3 years",
        "retention_days": 1095,
        "action_on_expiry": "review",  # Should normalize to uppercase
        "description": "Demo transaction rule",
        "is_active": True
    }
    schema = PolicyRuleCreate(**valid_data)
    assert schema.action_on_expiry == "REVIEW"

    # Invalid action_on_expiry
    with pytest.raises(ValueError):
        PolicyRuleCreate(
            rule_code="POL-INV",
            name="Invalid Policy",
            category="Customer",
            retention_period="1 year",
            retention_days=365,
            action_on_expiry="INVALID_ACTION"
        )

def test_lifecycle_action_schema_validation():
    # Valid actions
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE", "keep", "delete"]:
        req = LifecycleActionRequest(action=action, reason="Test justification")
        assert req.action == action.upper()

    # Invalid action
    with pytest.raises(ValueError):
        LifecycleActionRequest(action="PURGE", reason="Not allowed")

def test_policy_evaluation_summary_schema():
    item = PolicyEvaluationItem(
        record_id="CUS-1001",
        category="Customer",
        expiry_date="2025-01-15",
        expiry_status="EXPIRED",
        days_until_expiry=-100,
        deterministic_recommendation="REVIEW",
        matched_policy_rule="POL-CUS-01",
        ai_recommendation="DELETE",
        purpose_mismatch=True,
        evaluation_reason="Overridden to REVIEW due to purpose mismatch"
    )

    summary = PolicyEvaluationSummary(
        total_evaluated=1,
        active_count=0,
        expiring_soon_count=0,
        expired_count=1,
        recommendations={"KEEP": 0, "REVIEW": 1, "ANONYMIZE": 0, "DELETE": 0},
        as_of_date="2026-10-04",
        expiring_soon_days=30,
        records=[item]
    )

    assert summary.total_evaluated == 1
    assert summary.records[0].record_id == "CUS-1001"
    assert summary.records[0].deterministic_recommendation == "REVIEW"
