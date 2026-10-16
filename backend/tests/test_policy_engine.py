import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.data_record import DataRecordModel
from app.models.policy import PolicyRuleModel
from app.schemas.policy import PolicyRuleCreate, PolicyRuleUpdate
from app.services.policy_service import PolicyService

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

# ---------------------------------------------------------------------------
# Duration Parsing Tests (Requirements 1 - 4)
# ---------------------------------------------------------------------------

def test_duration_parsing_2_years():
    assert PolicyService.parse_duration_to_days("2 years") == 730

def test_duration_parsing_3_years():
    assert PolicyService.parse_duration_to_days("3 years") == 1095

def test_duration_parsing_90_days():
    assert PolicyService.parse_duration_to_days("90 days") == 90
    assert PolicyService.parse_duration_to_days("180 days") == 180
    assert PolicyService.parse_duration_to_days("365 days") == 365
    assert PolicyService.parse_duration_to_days("1 year") == 365

def test_invalid_duration_rejected():
    with pytest.raises(ValueError):
        PolicyService.parse_duration_to_days("invalid_duration")
    with pytest.raises(ValueError):
        PolicyService.parse_duration_to_days("")
    with pytest.raises(ValueError):
        PolicyService.parse_duration_to_days("-5 days")

# ---------------------------------------------------------------------------
# Expiry Evaluation Tests (Requirements 5 - 9)
# ---------------------------------------------------------------------------

def test_active_expiry_status():
    # As of 2026-01-01, expiry 2026-06-01 is 151 days away (> 30 days) -> ACTIVE
    status, delta = PolicyService.evaluate_expiry(
        expiry_date_str="2026-06-01",
        as_of_date=date(2026, 1, 1),
        expiring_soon_days=30
    )
    assert status == "ACTIVE"
    assert delta == 151

def test_expiring_soon_expiry_status():
    # As of 2026-01-01, expiry 2026-01-20 is 19 days away (0 <= delta <= 30) -> EXPIRING_SOON
    status, delta = PolicyService.evaluate_expiry(
        expiry_date_str="2026-01-20",
        as_of_date=date(2026, 1, 1),
        expiring_soon_days=30
    )
    assert status == "EXPIRING_SOON"
    assert delta == 19

def test_expired_expiry_status():
    # As of 2026-01-01, expiry 2025-12-15 is -17 days away (< 0) -> EXPIRED
    status, delta = PolicyService.evaluate_expiry(
        expiry_date_str="2025-12-15",
        as_of_date=date(2026, 1, 1),
        expiring_soon_days=30
    )
    assert status == "EXPIRED"
    assert delta == -17

def test_custom_expiring_soon_days():
    # 45 days away with threshold 60 -> EXPIRING_SOON
    status1, _ = PolicyService.evaluate_expiry(
        expiry_date_str="2026-02-15",
        as_of_date=date(2026, 1, 1),
        expiring_soon_days=60
    )
    assert status1 == "EXPIRING_SOON"

    # 45 days away with threshold 30 -> ACTIVE
    status2, _ = PolicyService.evaluate_expiry(
        expiry_date_str="2026-02-15",
        as_of_date=date(2026, 1, 1),
        expiring_soon_days=30
    )
    assert status2 == "ACTIVE"

def test_custom_as_of_date_works():
    # Check that as_of_date determines status dynamically without hardcoding
    status_past, delta_past = PolicyService.evaluate_expiry(
        expiry_date_str="2026-05-01",
        as_of_date=date(2025, 5, 1)
    )
    assert status_past == "ACTIVE"

    status_future, delta_future = PolicyService.evaluate_expiry(
        expiry_date_str="2026-05-01",
        as_of_date=date(2026, 5, 2)
    )
    assert status_future == "EXPIRED"

# ---------------------------------------------------------------------------
# Deterministic Governance Decision Tests (Requirements 10 - 13)
# ---------------------------------------------------------------------------

def test_purpose_mismatch_forces_review_when_ai_says_delete(db_session):
    record = DataRecordModel(
        record_id="REC-001",
        data_type="Customer Profile",
        category="Customer",
        sensitivity="High",
        collection_purpose="Billing",
        current_usage="Secondary Marketing",
        owner="Finance",
        created_date="2023-01-01",
        retention_period="2 years",
        expiry_date="2025-01-01",
        status="Expired",
        source="CRM",
        purpose_mismatch=True,
        ai_recommendation="DELETE"
    )
    db_session.add(record)
    db_session.commit()

    evaluation = PolicyService.evaluate_record(
        db=db_session,
        record=record,
        as_of_date=date(2026, 1, 1)
    )
    # Even though AI says DELETE and record is EXPIRED, purpose_mismatch strictly mandates REVIEW
    assert evaluation.deterministic_recommendation == "REVIEW"
    assert evaluation.ai_recommendation == "DELETE"
    assert evaluation.purpose_mismatch is True
    assert "Purpose mismatch detected" in evaluation.evaluation_reason

def test_purpose_mismatch_forces_review_when_ai_says_keep(db_session):
    record = DataRecordModel(
        record_id="REC-002",
        data_type="Transaction Log",
        category="Transaction",
        sensitivity="Medium",
        collection_purpose="Tax Audit",
        current_usage="Profiling",
        owner="Audit",
        created_date="2025-01-01",
        retention_period="3 years",
        expiry_date="2028-01-01",
        status="Active",
        source="ERP",
        purpose_mismatch=True,
        ai_recommendation="KEEP"
    )
    db_session.add(record)
    db_session.commit()

    evaluation = PolicyService.evaluate_record(
        db=db_session,
        record=record,
        as_of_date=date(2026, 1, 1)
    )
    assert evaluation.deterministic_recommendation == "REVIEW"
    assert evaluation.ai_recommendation == "KEEP"

def test_expired_record_follows_configured_policy_action(db_session):
    # Setup specific policy: Marketing -> DELETE on expiry
    policy = PolicyRuleModel(
        rule_code="POL-MKT-01",
        name="Marketing Demo Policy",
        category="Marketing",
        retention_period="1 year",
        retention_days=365,
        action_on_expiry="DELETE",
        is_active=True
    )
    db_session.add(policy)

    record = DataRecordModel(
        record_id="MKT-100",
        data_type="Ad Campaign Leads",
        category="Marketing",
        sensitivity="Low",
        collection_purpose="Lead Generation",
        current_usage="Lead Generation",
        owner="Marketing",
        created_date="2024-01-01",
        retention_period="1 year",
        expiry_date="2025-01-01",
        status="Expired",
        source="Web Leads",
        purpose_mismatch=False,
        ai_recommendation="REVIEW"
    )
    db_session.add(record)
    db_session.commit()

    evaluation = PolicyService.evaluate_record(
        db=db_session,
        record=record,
        as_of_date=date(2026, 1, 1)
    )
    # Expired with NO purpose mismatch: follows policy action_on_expiry ("DELETE")
    assert evaluation.deterministic_recommendation == "DELETE"
    assert evaluation.matched_policy_rule == "POL-MKT-01"
    assert evaluation.expiry_status == "EXPIRED"

def test_category_specific_policy_beats_wildcard_fallback(db_session):
    # Add wildcard policy
    wildcard = PolicyRuleModel(
        rule_code="POL-GEN-GLOBAL",
        name="Global Catchall",
        category="*",
        retention_period="5 years",
        retention_days=1825,
        action_on_expiry="ANONYMIZE",
        is_active=True
    )
    # Add category-specific policy
    customer_pol = PolicyRuleModel(
        rule_code="POL-CUS-SPECIFIC",
        name="Customer Specific",
        category="Customer",
        retention_period="2 years",
        retention_days=730,
        action_on_expiry="REVIEW",
        is_active=True
    )
    db_session.add_all([wildcard, customer_pol])
    db_session.commit()

    matched = PolicyService.match_policy(db_session, "Customer")
    assert matched.rule_code == "POL-CUS-SPECIFIC"

    # For an unknown category, it should fall back to wildcard
    matched_fallback = PolicyService.match_policy(db_session, "UnknownCategory")
    assert matched_fallback.rule_code == "POL-GEN-GLOBAL"

# ---------------------------------------------------------------------------
# Policy CRUD Tests
# ---------------------------------------------------------------------------

def test_policy_crud_operations(db_session):
    # Create
    create_schema = PolicyRuleCreate(
        rule_code="POL-CRUD-01",
        name="CRUD Test Policy",
        category="Financial",
        retention_period="7 years",
        retention_days=2555,
        action_on_expiry="ANONYMIZE",
        is_active=True
    )
    created = PolicyService.create_policy(db_session, create_schema)
    assert created.id is not None
    assert created.rule_code == "POL-CRUD-01"

    # Duplicate code rejected
    with pytest.raises(ValueError):
        PolicyService.create_policy(db_session, create_schema)

    # Get
    fetched = PolicyService.get_policy(db_session, created.id)
    assert fetched is not None
    assert fetched.name == "CRUD Test Policy"

    # List
    policies = PolicyService.list_policies(db_session, active_only=True)
    assert len(policies) >= 1

    # Update
    update_schema = PolicyRuleUpdate(name="Updated Financial Policy", action_on_expiry="DELETE")
    updated = PolicyService.update_policy(db_session, created.id, update_schema)
    assert updated.name == "Updated Financial Policy"
    assert updated.action_on_expiry == "DELETE"

    # Deactivate (soft delete, row preserved)
    deactivated = PolicyService.deactivate_policy(db_session, created.id)
    assert deactivated.is_active is False

    # Row still exists in DB
    raw_query = db_session.query(PolicyRuleModel).filter_by(id=created.id).first()
    assert raw_query is not None
    assert raw_query.is_active is False
