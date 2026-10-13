"""
DATAEXPIRY — AI Service & Purpose Mismatch Engine Tests
Tests purpose mismatch detection, equivalent wording, ambiguous metadata,
risk scoring, lifecycle recommendations (KEEP, REVIEW, ANONYMIZE, DELETE),
and API endpoints.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import httpx
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


# ==============================================================================
# Unit & Integration Tests for Google Gemini Semantic AI Provider (Team Member 2)
# ==============================================================================

def make_mock_gemini_response(payload_dict: dict, status_code: int = 200):
    """Helper to generate a mock httpx.Response resembling Google Gemini REST API."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if status_code == 200:
        gemini_body = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": json.dumps(payload_dict)}
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP",
                    "index": 0
                }
            ]
        }
        mock_resp.json.return_value = gemini_body
    else:
        mock_resp.json.return_value = {"error": {"message": "API Error", "code": status_code}}
    return mock_resp


def test_gemini_successful_response_ai_assisted(monkeypatch):
    """Test A & B: Successful Gemini response produces ai_assisted mode and valid structure."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-valid-key")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-1.5-flash")

    mock_gemini_output = {
        "purpose_mismatch": True,
        "risk_level": "High",
        "ai_recommendation": "REVIEW",
        "explanation": "Active marketing campaigns diverge from stated order fulfillment consent (Advisory only)."
    }

    mock_response = make_mock_gemini_response(mock_gemini_output)

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = AIService.analyze_record({
            "record_id": "GEM-001",
            "category": "Customer",
            "sensitivity": "Medium",
            "collection_purpose": "Order Fulfillment",
            "current_usage": "Targeted Marketing Campaigns",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert mock_post.called
        assert result["analysis_mode"] == "ai_assisted"
        assert result["purpose_mismatch"] is True
        assert result["risk_level"] == "High"
        assert result["ai_recommendation"] == "REVIEW"
        assert result["explanation"] == "Active marketing campaigns diverge from stated order fulfillment consent (Advisory only)."
        assert result["record_id"] == "GEM-001"


def test_gemini_privacy_safe_request_payload(monkeypatch):
    """Test C: Verifies ONLY privacy-safe governance metadata is transmitted to Gemini."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "secret-test-key")

    mock_gemini_output = {
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Semantically aligned with operational goals (Advisory only)."
    }
    mock_response = make_mock_gemini_response(mock_gemini_output)

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        # Pass a record with sensitive fields present in the record dict
        AIService.analyze_record({
            "record_id": "SENSITIVE-RECORD-ID-9999",
            "customer_name": "Jane Doe",
            "email": "jane.doe@example.com",
            "credit_card": "4111-2222-3333-4444",
            "category": "Financial",
            "sensitivity": "High",
            "collection_purpose": "Billing and Invoice Processing",
            "current_usage": "Billing Settlement",
            "status": "Active",
            "expiry_date": "2028-12-31"
        })

        assert mock_post.called
        args, kwargs = mock_post.call_args

        # Inspect headers for x-goog-api-key
        headers = kwargs.get("headers", {})
        assert headers.get("x-goog-api-key") == "secret-test-key"

        # Inspect URL and request payload
        url = args[0] if args else kwargs.get("url", "")
        assert "generativelanguage.googleapis.com" in url

        json_payload = kwargs.get("json", {})
        prompt_text = json_payload["contents"][0]["parts"][0]["text"]

        # Ensure privacy boundary: governance metadata IS present
        assert "Billing and Invoice Processing" in prompt_text
        assert "Billing Settlement" in prompt_text
        assert "Financial" in prompt_text
        assert "High" in prompt_text

        # Ensure privacy boundary: PII and raw IDs ARE NEVER transmitted
        assert "SENSITIVE-RECORD-ID-9999" not in prompt_text
        assert "Jane Doe" not in prompt_text
        assert "jane.doe@example.com" not in prompt_text
        assert "4111-2222-3333-4444" not in prompt_text


def test_gemini_http_failure_triggers_rule_based_fallback(monkeypatch):
    """Test D: HTTP 500 error from Gemini triggers deterministic rule-based fallback."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-valid-key")

    mock_response = make_mock_gemini_response({}, status_code=500)

    with patch("httpx.Client.post", return_value=mock_response):
        result = AIService.analyze_record({
            "record_id": "ERR-500",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Order Processing",
            "current_usage": "Targeted Marketing Campaigns",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        # Rule-based engine correctly flags marketing creep
        assert result["purpose_mismatch"] is True
        assert result["risk_level"] in {"High", "Critical"}
        assert result["ai_recommendation"] == "REVIEW"


def test_gemini_timeout_triggers_rule_based_fallback(monkeypatch):
    """Test E: Network timeout triggers deterministic rule-based fallback."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-valid-key")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timeout")):
        result = AIService.analyze_record({
            "record_id": "TIME-OUT",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Support Ticket Resolution",
            "current_usage": "Support Desk Inquiries",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert result["ai_recommendation"] == "KEEP"


def test_no_api_key_defaults_to_rule_based(monkeypatch):
    """Test F: Missing API key executes rule-based engine directly without HTTP calls."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "")
    monkeypatch.setattr("app.core.config.settings.AI_API_KEY", "")

    with patch("httpx.Client.post") as mock_post:
        result = AIService.analyze_record({
            "record_id": "NO-KEY",
            "category": "Employee",
            "sensitivity": "High",
            "collection_purpose": "Payroll Processing",
            "current_usage": "Salary Disbursement",
            "status": "Active",
            "expiry_date": "2026-12-31"
        })

        assert not mock_post.called
        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert result["ai_recommendation"] == "KEEP"


def test_gemini_invalid_json_triggers_rule_based_fallback(monkeypatch):
    """Test G: Invalid/malformed JSON returned by LLM triggers rule-based fallback."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-valid-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "I am an AI and cannot generate JSON: error 404"}]
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        result = AIService.analyze_record({
            "record_id": "BAD-JSON",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Order Delivery",
            "current_usage": "Order Delivery",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert result["ai_recommendation"] == "KEEP"


def test_gemini_invalid_risk_or_recommendation_triggers_rule_based_fallback(monkeypatch):
    """Test H: Invalid enum values from LLM (e.g. unknown recommendation) trigger fallback."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-valid-key")

    # Invalid recommendation "DESTROY" and risk "Catastrophic"
    invalid_gemini_output = {
        "purpose_mismatch": True,
        "risk_level": "Catastrophic",
        "ai_recommendation": "DESTROY",
        "explanation": "Non-compliant"
    }
    mock_response = make_mock_gemini_response(invalid_gemini_output)

    with patch("httpx.Client.post", return_value=mock_response):
        result = AIService.analyze_record({
            "record_id": "BAD-ENUM",
            "category": "Customer",
            "sensitivity": "Medium",
            "collection_purpose": "User Profile",
            "current_usage": "User Profile",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert result["ai_recommendation"] == "KEEP"