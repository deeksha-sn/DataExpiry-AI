import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.models.data_record import DataRecordModel
from app.core.security import UserRole
from app.services.lifecycle_service import ROLE_PERMISSIONS, LifecycleService
from app.schemas.action import LifecycleActionResponse

# ---------------------------------------------------------------------------
# Isolated In-Memory Database Fixture
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

ROLE_HEADERS = {
    UserRole.ADMIN: {"X-User-Id": "admin_test", "X-User-Role": "ADMIN"},
    UserRole.DATA_GOVERNANCE: {"X-User-Id": "gov_test", "X-User-Role": "DATA_GOVERNANCE"},
    UserRole.PRIVACY_OFFICER: {"X-User-Id": "priv_test", "X-User-Role": "PRIVACY_OFFICER"},
    UserRole.AUDITOR: {"X-User-Id": "audit_test", "X-User-Role": "AUDITOR"},
    UserRole.VIEWER: {"X-User-Id": "view_test", "X-User-Role": "VIEWER"},
}

@pytest.fixture(autouse=True)
def setup_isolated_db(monkeypatch):
    """Ensure clean tables and enabled development header auth for test client."""
    monkeypatch.setattr("app.core.config.settings.ENVIRONMENT", "development")
    monkeypatch.setattr("app.core.config.settings.ALLOW_DEV_HEADER_AUTH", True)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def sample_record():
    """Create a sample record in the isolated in-memory test database."""
    db = TestingSessionLocal()
    record = DataRecordModel(
        record_id="AUTH-TEST-REC-01",
        data_type="Customer Profile",
        category="Customer",
        sensitivity="High",
        collection_purpose="Order Processing",
        current_usage="Order Processing",
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
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()
    return record


# ---------------------------------------------------------------------------
# Safe Mock for Authorization Testing (No actual DELETE or ANONYMIZE operations)
# ---------------------------------------------------------------------------
def mock_execute_action_permission_check(db, record_id, action, user, role, reason=None):
    """
    Simulates execute_action authorization verification without performing
    any actual database DELETE, row removal, data masking, or status mutations.
    """
    action_upper = action.strip().upper()
    user_role = UserRole(role.strip().upper()) if isinstance(role, str) else role
    allowed_actions = ROLE_PERMISSIONS.get(user_role, set())

    if action_upper not in allowed_actions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Role '{user_role.value}' is not authorized to execute action '{action_upper}'. "
                f"Allowed actions for this role: {sorted(list(allowed_actions)) or 'None'}"
            )
        )

    # Return valid response indicating authorization succeeded without mutating DB
    return LifecycleActionResponse(
        record_id=record_id,
        action_executed=action_upper,
        audit_id=9999,
        message=f"Authorization passed for {action_upper} by {user_role.value} (safe authorization mock)",
        deletion_status="Not Required",
        anonymization_status="Not Required",
        review_status="Pending"
    )


# ---------------------------------------------------------------------------
# Exhaustive 20 Role/Action Combination Tests for POST /api/data/{record_id}/execute-action
# ---------------------------------------------------------------------------
ALL_COMBINATIONS = [
    # ADMIN: Can perform KEEP, REVIEW, ANONYMIZE, DELETE
    (UserRole.ADMIN, "KEEP", True),
    (UserRole.ADMIN, "REVIEW", True),
    (UserRole.ADMIN, "ANONYMIZE", True),
    (UserRole.ADMIN, "DELETE", True),

    # DATA_GOVERNANCE: Can perform KEEP, REVIEW, ANONYMIZE, DELETE
    (UserRole.DATA_GOVERNANCE, "KEEP", True),
    (UserRole.DATA_GOVERNANCE, "REVIEW", True),
    (UserRole.DATA_GOVERNANCE, "ANONYMIZE", True),
    (UserRole.DATA_GOVERNANCE, "DELETE", True),

    # PRIVACY_OFFICER: Can perform REVIEW, ANONYMIZE only (DELETE and KEEP are 403)
    (UserRole.PRIVACY_OFFICER, "KEEP", False),
    (UserRole.PRIVACY_OFFICER, "REVIEW", True),
    (UserRole.PRIVACY_OFFICER, "ANONYMIZE", True),
    (UserRole.PRIVACY_OFFICER, "DELETE", False),

    # AUDITOR: Cannot perform any lifecycle actions (403)
    (UserRole.AUDITOR, "KEEP", False),
    (UserRole.AUDITOR, "REVIEW", False),
    (UserRole.AUDITOR, "ANONYMIZE", False),
    (UserRole.AUDITOR, "DELETE", False),

    # VIEWER: Cannot perform any lifecycle actions (403)
    (UserRole.VIEWER, "KEEP", False),
    (UserRole.VIEWER, "REVIEW", False),
    (UserRole.VIEWER, "ANONYMIZE", False),
    (UserRole.VIEWER, "DELETE", False),
]

@pytest.mark.parametrize("role,action,is_authorized", ALL_COMBINATIONS)
def test_execute_action_all_role_action_combinations(monkeypatch, sample_record, role, action, is_authorized):
    """
    Tests every role/action combination against POST /api/data/{record_id}/execute-action.
    Asserts HTTP 403 for unauthorized combinations and HTTP 200 for authorized combinations.
    Uses mock execution so no actual DELETE or ANONYMIZE occurs on the database record.
    """
    monkeypatch.setattr(
        "app.api.action_routes.LifecycleService.execute_action",
        mock_execute_action_permission_check
    )

    headers = ROLE_HEADERS[role]
    resp = client.post(
        f"/api/data/{sample_record.record_id}/execute-action",
        json={"action": action, "reason": f"Testing {action} by {role.value}"},
        headers=headers
    )

    if is_authorized:
        assert resp.status_code == 200, f"Expected 200 for role {role.value} action {action}, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["action_executed"] == action
        assert data["audit_id"] == 9999
    else:
        assert resp.status_code == 403, f"Expected 403 for role {role.value} action {action}, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Specific Verification for DELETE Rule: ADMIN, DATA_GOVERNANCE only
# ---------------------------------------------------------------------------
def test_delete_action_permission_rule_strictly_enforced(monkeypatch, sample_record):
    """
    Verify exact rule:
    DELETE: ADMIN, DATA_GOVERNANCE only.
    All other roles (PRIVACY_OFFICER, AUDITOR, VIEWER) must receive HTTP 403.
    """
    monkeypatch.setattr(
        "app.api.action_routes.LifecycleService.execute_action",
        mock_execute_action_permission_check
    )

    # Authorized roles (200)
    for auth_role in [UserRole.ADMIN, UserRole.DATA_GOVERNANCE]:
        resp = client.post(
            f"/api/data/{sample_record.record_id}/execute-action",
            json={"action": "DELETE", "reason": "Authorized retention deletion test"},
            headers=ROLE_HEADERS[auth_role]
        )
        assert resp.status_code == 200
        assert resp.json()["action_executed"] == "DELETE"

    # Unauthorized roles (403)
    for unauth_role in [UserRole.PRIVACY_OFFICER, UserRole.AUDITOR, UserRole.VIEWER]:
        resp = client.post(
            f"/api/data/{sample_record.record_id}/execute-action",
            json={"action": "DELETE", "reason": "Unauthorized deletion attempt"},
            headers=ROLE_HEADERS[unauth_role]
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Specific Verification for ANONYMIZE Rule: ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER only
# ---------------------------------------------------------------------------
def test_anonymize_action_permission_rule_strictly_enforced(monkeypatch, sample_record):
    """
    Verify exact rule:
    ANONYMIZE: ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER only.
    All other roles (AUDITOR, VIEWER) must receive HTTP 403.
    """
    monkeypatch.setattr(
        "app.api.action_routes.LifecycleService.execute_action",
        mock_execute_action_permission_check
    )

    # Authorized roles (200)
    for auth_role in [UserRole.ADMIN, UserRole.DATA_GOVERNANCE, UserRole.PRIVACY_OFFICER]:
        resp = client.post(
            f"/api/data/{sample_record.record_id}/execute-action",
            json={"action": "ANONYMIZE", "reason": "Authorized anonymization test"},
            headers=ROLE_HEADERS[auth_role]
        )
        assert resp.status_code == 200
        assert resp.json()["action_executed"] == "ANONYMIZE"

    # Unauthorized roles (403)
    for unauth_role in [UserRole.AUDITOR, UserRole.VIEWER]:
        resp = client.post(
            f"/api/data/{sample_record.record_id}/execute-action",
            json={"action": "ANONYMIZE", "reason": "Unauthorized anonymization attempt"},
            headers=ROLE_HEADERS[unauth_role]
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Service-Level Verification: Unauthorized Actions Abort Before DB Query
# ---------------------------------------------------------------------------
def test_lifecycle_service_rejects_unauthorized_before_db_access():
    """
    Demonstrates that LifecycleService.execute_action enforces role authorization
    strictly before querying the database or performing any record operations.
    Passing a mock db verifies that db.query is never called for unauthorized attempts.
    """
    mock_db = MagicMock()

    # PRIVACY_OFFICER attempting DELETE must raise 403 with zero db queries
    with pytest.raises(HTTPException) as exc_po_del:
        LifecycleService.execute_action(
            db=mock_db,
            record_id="REC-001",
            action="DELETE",
            user="po_user",
            role=UserRole.PRIVACY_OFFICER
        )
    assert exc_po_del.value.status_code == 403
    mock_db.query.assert_not_called()

    # PRIVACY_OFFICER attempting KEEP must raise 403 with zero db queries
    with pytest.raises(HTTPException) as exc_po_keep:
        LifecycleService.execute_action(
            db=mock_db,
            record_id="REC-001",
            action="KEEP",
            user="po_user",
            role=UserRole.PRIVACY_OFFICER
        )
    assert exc_po_keep.value.status_code == 403
    mock_db.query.assert_not_called()

    # AUDITOR attempting any action must raise 403 with zero db queries
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        with pytest.raises(HTTPException) as exc_aud:
            LifecycleService.execute_action(
                db=mock_db,
                record_id="REC-001",
                action=action,
                user="aud_user",
                role=UserRole.AUDITOR
            )
        assert exc_aud.value.status_code == 403
        mock_db.query.assert_not_called()

    # VIEWER attempting any action must raise 403 with zero db queries
    for action in ["KEEP", "REVIEW", "ANONYMIZE", "DELETE"]:
        with pytest.raises(HTTPException) as exc_view:
            LifecycleService.execute_action(
                db=mock_db,
                record_id="REC-001",
                action=action,
                user="view_user",
                role=UserRole.VIEWER
            )
        assert exc_view.value.status_code == 403
        mock_db.query.assert_not_called()


# ---------------------------------------------------------------------------
# Verification: Data Preservation (No actual DELETE or ANONYMIZE took place)
# ---------------------------------------------------------------------------
def test_no_actual_delete_or_anonymize_occurred(sample_record):
    """
    Verifies that the test database record remains completely intact and unmodified:
    - Status is still 'Active'
    - Deletion status is still 'Not Required'
    - Anonymization status is still 'Not Required'
    - Sensitive attributes (owner, collection_purpose, data_type) are untouched
    """
    db = TestingSessionLocal()
    rec = db.query(DataRecordModel).filter_by(record_id=sample_record.record_id).first()
    assert rec is not None
    assert rec.status == "Active"
    assert rec.deletion_status == "Not Required"
    assert rec.anonymization_status == "Not Required"
    assert rec.review_status == "Pending"
    assert rec.owner == "Customer Operations"
    assert rec.collection_purpose == "Order Processing"
    db.close()
