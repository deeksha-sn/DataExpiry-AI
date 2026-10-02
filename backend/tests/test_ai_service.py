"""
DATAEXPIRY — AI Service & Purpose Mismatch Engine Tests
Tests purpose mismatch detection, equivalent wording, ambiguous metadata,
risk scoring, lifecycle recommendations (KEEP, REVIEW, ANONYMIZE, DELETE),
and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.services.ai_service import AIService
from app.models.data_record import DataRecordModel

# Setup in-memory SQLite DB for testing
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


# ==============================================================================
# Unit Tests for Purpose Mismatch Logic & Recommendations
# ==============================================================================

def test_identical_purpose_and_usage():
    """Identical text must never be flagged as a mismatch and recommend KEEP."""
    result = AIService.analyze_record({
        "record_id": "TEST-101",
        "category": "Customer",
        "sensitivity": "Low",
        "collection_purpose": "Order Processing & Delivery",
        "current_usage": "Order Processing & Delivery",
        "status": "Active",
        "expiry_date": "2027-01-01"
    })
    assert result["purpose_mismatch"] is False
    assert result["risk_level"] == "Low"
    assert result["ai_recommendation"] == "KEEP"
    assert result["analysis_mode"] == "rule_based"
    assert "PURPOSE COMPLIANT" in result["explanation"]


def test_equivalent_wording_domain_matching():
    """Different phrasing with equivalent operational domain must match and recommend KEEP."""
    result = AIService.analyze_record({
        "record_id": "TEST-102",
        "category": "Customer",
        "sensitivity": "Medium",
        "collection_purpose": "Customer Support Resolution",
        "current_usage": "Helpdesk Ticket Inquiries & Assistance",
        "status": "Active",
        "expiry_date": "2027-05-01"
    })
    assert result["purpose_mismatch"] is False
    assert result["risk_level"] == "Low"
    assert result["ai_recommendation"] == "KEEP"
    assert "Semantically compatible" in result["explanation"]


def test_purpose_mismatch_marketing_creep():
    """Secondary marketing usage without consent must trigger purpose mismatch."""
    result = AIService.analyze_record({
        "record_id": "TEST-103",
        "category": "Customer",
        "sensitivity": "High",
        "collection_purpose": "Account Management",
        "current_usage": "Targeted Marketing Campaigns & Promotional Upselling",
        "status": "Active",
        "expiry_date": "2027-01-01"
    })
    assert result["purpose_mismatch"] is True
    assert result["risk_level"] in {"High", "Critical"}
    assert result["ai_recommendation"] == "REVIEW"  # Active record needs human review
    assert "Unauthorized purpose creep" in result["explanation"]


def test_purpose_mismatch_ai_training_creep():
    """Repurposing recruiting data for AI model training must trigger mismatch."""
    result = AIService.analyze_record({
        "record_id": "TEST-104",
        "category": "Employee",
        "sensitivity": "High",
        "collection_purpose": "Recruitment & Assessment",
        "current_usage": "AI Resume Screening Training & Model Tuning",
        "status": "Active",
        "expiry_date": "2026-11-01"
    })
    assert result["purpose_mismatch"] is True
    assert result["ai_recommendation"] == "REVIEW"
    assert "AI ML Training" in result["explanation"] or "ai model training" in result["explanation"].lower()


def test_ambiguous_and_missing_metadata():
    """Empty or placeholder metadata must return REVIEW without false-positive critical alarms."""
    result = AIService.analyze_record({
        "record_id": "TEST-105",
        "category": "Customer",
        "sensitivity": "Low",
        "collection_purpose": "N/A",
        "current_usage": "Unknown",
        "status": "Active",
        "expiry_date": "2026-12-31"
    })
    assert result["purpose_mismatch"] is False
    assert result["ai_recommendation"] == "REVIEW"
    assert "Review required" in result["explanation"] or "Ambiguous" in result["explanation"]


def test_expired_record_with_purpose_mismatch_recommends_delete():
    """Expired record combined with purpose mismatch represents critical non-compliance -> DELETE."""
    result = AIService.analyze_record({
        "record_id": "TEST-106",
        "category": "Transaction",
        "sensitivity": "High",
        "collection_purpose": "UI Experience Optimization",
        "current_usage": "Third-Party Data Broker Monetization",
        "status": "Expired",
        "expiry_date": "2024-01-01"
    })
    assert result["purpose_mismatch"] is True
    assert result["risk_level"] == "Critical"
    assert result["ai_recommendation"] == "DELETE"
    assert "Recommendation: DELETE" in result["explanation"]


def test_expired_high_sensitivity_recommends_anonymize():
    """Expired high-sensitivity record with no purpose violation -> ANONYMIZE."""
    result = AIService.analyze_record({
        "record_id": "TEST-107",
        "category": "Financial",
        "sensitivity": "High",
        "collection_purpose": "Tax & Legal Audit Compliance",
        "current_usage": "Tax Audit Reporting",
        "status": "Expired",
        "expiry_date": "2024-06-30"
    })
    assert result["purpose_mismatch"] is False
    assert result["risk_level"] in {"High", "Medium"}
    assert result["ai_recommendation"] == "ANONYMIZE"
    assert "Recommendation: ANONYMIZE" in result["explanation"]


def test_expiring_soon_recommends_review():
    """Expiring soon record must trigger REVIEW for upcoming retention decision."""
    result = AIService.analyze_record({
        "record_id": "TEST-108",
        "category": "Customer",
        "sensitivity": "Medium",
        "collection_purpose": "Loyalty Program Tracking",
        "current_usage": "Loyalty Rewards Management",
        "status": "Expiring Soon",
        "expiry_date": "2026-10-25"
    })
    assert result["purpose_mismatch"] is False
    assert result["risk_level"] == "Medium"
    assert result["ai_recommendation"] == "REVIEW"


def test_rule_based_fallback_mode():
    """When no external AI is configured, analysis_mode must be rule_based."""
    result = AIService.analyze_record({
        "record_id": "TEST-109",
        "category": "General",
        "sensitivity": "Low",
        "collection_purpose": "Physical Security Access",
        "current_usage": "Building Badge Access Logs",
        "status": "Active",
        "expiry_date": "2027-01-01"
    })
    assert result["analysis_mode"] == "rule_based"


# ==============================================================================
# API Endpoint Integration Tests
# ==============================================================================

def test_api_check_mismatch_playground_endpoint():
    """Test POST /api/ai/check-mismatch sandbox."""
    payload = {
        "collection_purpose": "Order Processing",
        "current_usage": "Targeted Marketing Campaigns",
        "category": "Customer",
        "sensitivity": "High",
        "status": "Active"
    }
    response = client.post("/api/ai/check-mismatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["purpose_mismatch"] is True
    assert data["risk_level"] in {"High", "Critical"}
    assert data["ai_recommendation"] == "REVIEW"
    assert data["analysis_mode"] == "rule_based"


def test_api_batch_analyze_and_summary_endpoints():
    """Test POST /api/ai/batch-analyze and GET /api/ai/summary on seeded DB."""
    app.dependency_overrides[get_db] = override_get_db
    # Seed a couple of records in testing DB
    db = TestingSessionLocal()
    rec1 = DataRecordModel(
        record_id="TST-AI-01",
        data_type="Test Order",
        category="Customer",
        sensitivity="Low",
        collection_purpose="Order Processing",
        current_usage="Order Delivery",
        owner="Logistics",
        created_date="2025-01-01",
        retention_period="2 years",
        expiry_date="2027-01-01",
        status="Active",
        source="Web"
    )
    rec2 = DataRecordModel(
        record_id="TST-AI-02",
        data_type="Test Marketing",
        category="Customer",
        sensitivity="High",
        collection_purpose="Support Desk",
        current_usage="Commercial Reselling & Data Broker",
        owner="Sales",
        created_date="2023-01-01",
        retention_period="1 year",
        expiry_date="2024-01-01",
        status="Expired",
        source="CRM"
    )
    db.add(rec1)
    db.add(rec2)
    db.commit()
    db.close()

    # Run batch analyze
    batch_resp = client.post("/api/ai/batch-analyze")
    assert batch_resp.status_code == 200
    batch_data = batch_resp.json()
    assert batch_data["total_analyzed"] >= 2
    assert batch_data["potential_mismatches"] >= 1
    assert "recommendations" in batch_data
    assert "risk_breakdown" in batch_data

    # Check single record analyze
    single_resp = client.post("/api/data/TST-AI-01/analyze")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["record_id"] == "TST-AI-01"
    assert single_data["purpose_mismatch"] is False
    assert single_data["ai_recommendation"] == "KEEP"

    # Check summary endpoint
    summary_resp = client.get("/api/ai/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["total_records"] >= 2
    assert "potential_mismatches" in summary_data
    assert "recommendations" in summary_data
