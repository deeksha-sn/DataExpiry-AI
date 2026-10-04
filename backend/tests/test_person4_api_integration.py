import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.models.data_record import DataRecordModel
from app.models.policy import PolicyRuleModel

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Ensure clean tables for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

# Helper role headers
ADMIN_HEADERS = {"X-User-Id": "admin_1", "X-User-Role": "ADMIN"}
GOVERNANCE_HEADERS = {"X-User-Id": "gov_1", "X-User-Role": "DATA_GOVERNANCE"}
PRIVACY_HEADERS = {"X-User-Id": "priv_1", "X-User-Role": "PRIVACY_OFFICER"}
AUDITOR_HEADERS = {"X-User-Id": "audit_1", "X-User-Role": "AUDITOR"}
VIEWER_HEADERS = {"X-User-Id": "view_1", "X-User-Role": "VIEWER"}

def create_sample_record(record_id="INT-REC-01", category="Customer", expiry="2025-01-01", mismatch=False):
    db = TestingSessionLocal()
    record = DataRecordModel(
        record_id=record_id,
        data_type="Customer Account",
        category=category,
        sensitivity="High",
        collection_purpose="Order Processing",
        current_usage="Secondary Profiling" if mismatch else "Order Processing",
        owner="Customer Success",
        created_date="2023-01-01",
        retention_period="2 years",
        expiry_date=expiry,
        status="Active",
        source="CRM DB",
        purpose_mismatch=mismatch,
        ai_recommendation="DELETE" if mismatch else "KEEP",
        review_status="Pending",
        anonymization_status="Not Required",
        deletion_status="Not Required"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()
    return record

# ---------------------------------------------------------------------------
# Policy CRUD API Tests
# ---------------------------------------------------------------------------

def test_api_policy_crud_flow():
    # 1. Create Policy (as DATA_GOVERNANCE)
    policy_payload = {
        "rule_code": "POL-API-01",
        "name": "API Test Customer Retention",
        "category": "Customer",
        "retention_period": "2 years",
        "retention_days": 730,
        "action_on_expiry": "REVIEW",
        "description": "Integration test rule",
        "is_active": True
    }
    create_resp = client.post("/api/policies", json=policy_payload, headers=GOVERNANCE_HEADERS)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["rule_code"] == "POL-API-01"
    policy_id = created_data["id"]

    # 2. Duplicate code rejected
    dup_resp = client.post("/api/policies", json=policy_payload, headers=GOVERNANCE_HEADERS)
    assert dup_resp.status_code == 400

    # 3. Get single policy
    get_resp = client.get(f"/api/policies/{policy_id}", headers=VIEWER_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "API Test Customer Retention"

    # 4. List policies
    list_resp = client.get("/api/policies", headers=VIEWER_HEADERS)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 5. Update policy
    update_resp = client.put(
        f"/api/policies/{policy_id}",
        json={"name": "Updated Retention Rule", "action_on_expiry": "ANONYMIZE"},
        headers=GOVERNANCE_HEADERS
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Retention Rule"
    assert update_resp.json()["action_on_expiry"] == "ANONYMIZE"

    # 6. Deactivate policy (DELETE soft-delete)
    del_resp = client.delete(f"/api/policies/{policy_id}", headers=ADMIN_HEADERS)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # List active only should now be 0
    active_resp = client.get("/api/policies?active_only=true", headers=VIEWER_HEADERS)
    assert len(active_resp.json()) == 0

# ---------------------------------------------------------------------------
# Policy Evaluation API Tests
# ---------------------------------------------------------------------------

def test_api_policy_evaluation_batch_and_single():
    # Setup policy & records
    client.post("/api/policies", json={
        "rule_code": "POL-DEMO-CUS",
        "name": "Customer Rule",
        "category": "Customer",
        "retention_period": "2 years",
        "retention_days": 730,
        "action_on_expiry": "REVIEW",
        "is_active": True
    }, headers=ADMIN_HEADERS)

    # Record 1: Expired + purpose mismatch -> MUST BE REVIEW
    create_sample_record("REC-EVAL-01", category="Customer", expiry="2025-01-01", mismatch=True)
    # Record 2: Active (expiry in 2028)
    create_sample_record("REC-EVAL-02", category="Customer", expiry="2028-01-01", mismatch=False)

    # Batch evaluate
    eval_resp = client.post(
        "/api/policies/evaluate?as_of_date=2026-01-01&expiring_soon_days=30",
        headers=AUDITOR_HEADERS
    )
    assert eval_resp.status_code == 200
    summary = eval_resp.json()
    assert summary["total_evaluated"] == 2
    assert summary["expired_count"] == 1
    assert summary["active_count"] == 1
    assert summary["recommendations"]["REVIEW"] >= 1
    assert summary["recommendations"]["KEEP"] >= 1

    # Single record evaluate
    single_eval_resp = client.post(
        "/api/policies/evaluate/REC-EVAL-01?as_of_date=2026-01-01",
        headers=PRIVACY_HEADERS
    )
    assert single_eval_resp.status_code == 200
    single_item = single_eval_resp.json()
    assert single_item["record_id"] == "REC-EVAL-01"
    assert single_item["deterministic_recommendation"] == "REVIEW"
    assert single_item["ai_recommendation"] == "DELETE"
    assert single_item["purpose_mismatch"] is True

# ---------------------------------------------------------------------------
# Lifecycle Action Execution API Tests
# ---------------------------------------------------------------------------

def test_api_execute_lifecycle_action_delete_simulation():
    rec = create_sample_record("REC-ACT-01")
    orig_owner = rec.owner
    orig_purpose = rec.collection_purpose

    # Execute DELETE via API as ADMIN
    action_resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "DELETE", "reason": "Simulated retention disposal"},
        headers=ADMIN_HEADERS
    )
    assert action_resp.status_code == 200
    data = action_resp.json()
    assert data["action_executed"] == "DELETE"
    assert data["deletion_status"] == "Deleted"
    assert data["audit_id"] is not None

    # Verify physical row and sensitive fields are preserved
    db = TestingSessionLocal()
    persisted = db.query(DataRecordModel).filter_by(record_id=rec.record_id).first()
    assert persisted is not None
    assert persisted.owner == orig_owner
    assert persisted.collection_purpose == orig_purpose
    assert persisted.deletion_status == "Deleted"
    db.close()

def test_api_execute_lifecycle_action_anonymize_and_review():
    rec = create_sample_record("REC-ACT-02")

    # Execute ANONYMIZE as DATA_GOVERNANCE
    anon_resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "ANONYMIZE", "reason": "De-identification protocol"},
        headers=GOVERNANCE_HEADERS
    )
    assert anon_resp.status_code == 200
    assert anon_resp.json()["anonymization_status"] == "Anonymized"
    assert anon_resp.json()["new_status"] == "Archived"

    # Execute REVIEW as PRIVACY_OFFICER
    rev_resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "REVIEW", "reason": "Human review queue"},
        headers=PRIVACY_HEADERS
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["review_status"] == "In Review"

# ---------------------------------------------------------------------------
# Audit API Tests
# ---------------------------------------------------------------------------

def test_api_audit_retrieval():
    rec = create_sample_record("REC-AUDIT-TEST")

    # Generate an action which creates an audit entry
    client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "KEEP", "reason": "Retention continuation"},
        headers=ADMIN_HEADERS
    )

    # Fetch audit logs as AUDITOR
    audit_resp = client.get("/api/audit", headers=AUDITOR_HEADERS)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) >= 1
    assert logs[0]["record_id"] == "REC-AUDIT-TEST"
    assert logs[0]["action"] == "KEEP"
    assert logs[0]["audit_id"] is not None
    assert logs[0]["created_at"] is not None

    # Fetch audit logs by record ID
    record_audit_resp = client.get(f"/api/audit/{rec.record_id}", headers=AUDITOR_HEADERS)
    assert record_audit_resp.status_code == 200
    rec_logs = record_audit_resp.json()
    assert len(rec_logs) == 1
    assert rec_logs[0]["record_id"] == rec.record_id

# ---------------------------------------------------------------------------
# RBAC Permissions API Tests
# ---------------------------------------------------------------------------

def test_api_rbac_permissions():
    rec = create_sample_record("REC-RBAC-01")

    # 1. VIEWER cannot create policies (403)
    resp = client.post("/api/policies", json={
        "rule_code": "POL-FAIL",
        "name": "Fail",
        "category": "Test",
        "retention_period": "1 year",
        "retention_days": 365,
        "action_on_expiry": "REVIEW"
    }, headers=VIEWER_HEADERS)
    assert resp.status_code == 403

    # 2. AUDITOR cannot create policies (403)
    resp = client.post("/api/policies", json={
        "rule_code": "POL-FAIL",
        "name": "Fail",
        "category": "Test",
        "retention_period": "1 year",
        "retention_days": 365,
        "action_on_expiry": "REVIEW"
    }, headers=AUDITOR_HEADERS)
    assert resp.status_code == 403

    # 3. VIEWER cannot execute lifecycle actions (403)
    resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "KEEP"},
        headers=VIEWER_HEADERS
    )
    assert resp.status_code == 403

    # 4. AUDITOR cannot execute lifecycle actions (403)
    resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "KEEP"},
        headers=AUDITOR_HEADERS
    )
    assert resp.status_code == 403

    # 5. PRIVACY_OFFICER cannot execute DELETE (403)
    resp = client.post(
        f"/api/data/{rec.record_id}/execute-action",
        json={"action": "DELETE"},
        headers=PRIVACY_HEADERS
    )
    assert resp.status_code == 403

    # 6. VIEWER cannot read audit logs (403)
    resp = client.get("/api/audit", headers=VIEWER_HEADERS)
    assert resp.status_code == 403
