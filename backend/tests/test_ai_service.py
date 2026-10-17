"""
DATAEXPIRY — AI Service & Purpose Mismatch Engine Tests
Tests purpose mismatch detection, equivalent wording, ambiguous metadata,
risk scoring, lifecycle recommendations (KEEP, REVIEW, ANONYMIZE, DELETE),
and API endpoints.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import threading
import time
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.services.ai_service import AIService, GeminiAIProvider
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


@pytest.fixture(autouse=True)
def isolate_ai_environment(monkeypatch, request):
    """
    Ensure automated unit tests run in isolation without making accidental
    external network calls to Google Gemini API.
    Rule-based tests run with GEMINI_API_KEY cleared so they evaluate deterministically.
    Tests specifically testing Gemini provider will set monkeypatch and mock httpx.
    """
    GeminiAIProvider.reset_cache_and_limiter()
    if not (request.node.name.startswith("test_gemini_") or request.node.name.startswith("test_try_ai_")):
        monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "")
        monkeypatch.setattr("app.core.config.settings.AI_API_KEY", "")


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
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.5-flash-lite")

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
            "collection_purpose": "Order Fulfillment",
            "current_usage": "Order Delivery Logistics",
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
            "collection_purpose": "User Profile Management",
            "current_usage": "User Authentication Services",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert result["ai_recommendation"] == "KEEP"


def test_try_ai_provider_invokes_gemini_provider_when_configured(monkeypatch):
    """Test I: Verify _try_ai_provider() invokes GeminiAIProvider.analyze() when valid API key is present."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "real-configured-key")

    mock_analysis = {
        "purpose_mismatch": True,
        "risk_level": "High",
        "ai_recommendation": "REVIEW",
        "explanation": "Active usage diverges from collection consent (Advisory only)."
    }

    with patch.object(GeminiAIProvider, "analyze", return_value=mock_analysis) as mock_analyze:
        result = AIService._try_ai_provider(
            record_id="REC-TRY-01",
            category="Customer",
            sensitivity="High",
            collection_purpose="Order Processing",
            current_usage="Ad Targeting",
            status="Active",
            expiry_date="2027-01-01"
        )

        assert mock_analyze.called
        assert result == mock_analysis
        # Verify privacy boundary: record_id was NOT forwarded to GeminiAIProvider.analyze
        call_kwargs = mock_analyze.call_args[1]
        assert "record_id" not in call_kwargs


def test_gemini_model_configurability_and_default(monkeypatch):
    """Test J: Verify Gemini model defaults to gemini-3.5-flash-lite and respects GEMINI_MODEL env var."""
    # When GEMINI_MODEL is empty, defaults to gemini-3.5-flash-lite
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "")
    assert GeminiAIProvider.get_model() == "gemini-3.5-flash-lite"

    # When GEMINI_MODEL is explicitly configured, it is used
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.8-flash")
    assert GeminiAIProvider.get_model() == "gemini-3.8-flash"

    # When model has 'models/' prefix, it is normalized
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "models/gemini-3.5-flash-lite")
    assert GeminiAIProvider.get_model() == "gemini-3.5-flash-lite"


def test_ai_recommendation_advisory_nature():
    """Test K: Verify AI recommendations are strictly advisory and do not perform state transitions."""
    result = AIService.analyze_record({
        "record_id": "REC-ADVISORY-01",
        "category": "Customer",
        "sensitivity": "High",
        "collection_purpose": "Order Processing",
        "current_usage": "Model Training",
        "status": "Active",
        "expiry_date=" : "2027-01-01"
    })

    # AI output contains recommendations and explanations, but is advisory only
    assert result["ai_recommendation"] in {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"}
    # The record's actual lifecycle status is not mutated by AI analysis
    assert result["category"] == "Customer"


def test_gemini_request_construction_endpoint_and_headers(monkeypatch):
    """Test L: Verify exact REST API URL, headers, and payload construction match Google Gemini spec."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-secret-key-12345")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.5-flash-lite")

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant usage."
    })

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = GeminiAIProvider.analyze(
            category="Operational",
            sensitivity="Medium",
            collection_purpose="Server Maintenance",
            current_usage="Server Log Diagnostics",
            status="Active",
            expiry_date="2027-12-31"
        )

        assert res is not None
        assert mock_post.called
        args, kwargs = mock_post.call_args

        # 1. Endpoint URL verification
        url = args[0] if args else kwargs.get("url", "")
        expected_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
        assert url == expected_url

        # 2. Header verification
        headers = kwargs.get("headers", {})
        assert headers.get("Content-Type") == "application/json"
        assert headers.get("x-goog-api-key") == "test-secret-key-12345"

        # 3. Payload and generationConfig verification
        json_payload = kwargs.get("json", {})
        assert "contents" in json_payload
        assert len(json_payload["contents"]) == 1
        parts = json_payload["contents"][0]["parts"]
        assert len(parts) == 1
        assert "text" in parts[0]
        assert "generationConfig" in json_payload
        assert json_payload["generationConfig"].get("responseMimeType") == "application/json"


def test_gemini_http_404_failure_logging_and_fallback(monkeypatch, caplog):
    """Test M: Verify HTTP 404 error (e.g. unavailable model) logs safely and falls back to rule-based engine."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-secret-key-404")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-2.5-flash")

    error_body = {
        "error": {
            "code": 404,
            "message": "This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash.",
            "status": "NOT_FOUND"
        }
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = json.dumps(error_body)
    mock_resp.json.return_value = error_body

    with patch("httpx.Client.post", return_value=mock_resp):
        result = AIService.analyze_record({
            "record_id": "REC-404-TEST",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Order Delivery",
            "current_usage": "Targeted Marketing Ads",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        # Rule-based fallback executes
        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is True

        # Diagnostic log contains status 404 and safely truncated message
        assert any(
            "HTTP status 404" in record.message and "is no longer available to new users" in record.message
            for record in caplog.records
        )
        # Verify secret was NEVER logged
        for record in caplog.records:
            assert "test-secret-key-404" not in record.message


def test_gemini_http_503_service_unavailable_fallback(monkeypatch, caplog):
    """Test N: Verify HTTP 503 high demand spike triggers fallback to rule-based engine."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-secret-key-503")

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = '{"error": {"code": 503, "message": "This model is currently experiencing high demand."}}'

    with patch("httpx.Client.post", return_value=mock_resp):
        result = AIService.analyze_record({
            "record_id": "REC-503-TEST",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Support Desk Operations",
            "current_usage": "Customer Helpdesk Inquiries",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["analysis_mode"] == "rule_based"
        assert result["purpose_mismatch"] is False
        assert any("HTTP status 503" in record.message for record in caplog.records)


def test_config_loads_backend_env_from_any_cwd(monkeypatch, tmp_path):
    """Test O: Verify Settings reliably loads backend/.env regardless of the process current working directory."""
    import os
    from app.core.config import Settings

    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        custom_settings = Settings()
        assert custom_settings.GEMINI_MODEL != ""
        # Default model is gemini-3.5-flash-lite
        assert custom_settings.GEMINI_MODEL in {"gemini-3.5-flash-lite", "gemini-3.8-flash"}
    finally:
        os.chdir(original_cwd)


def test_gemini_analyze_single_record_endpoint_ai_assisted(monkeypatch):
    """Test P: Verify POST /api/data/{record_id}/analyze returns ai_assisted when provider succeeds."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "valid-key-for-endpoint")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Seed test record in testing DB
    db = TestingSessionLocal()
    rec = DataRecordModel(
        record_id="REC-AI-EP-01",
        data_type="Customer Profile",
        category="Customer",
        sensitivity="High",
        collection_purpose="Account Security",
        current_usage="Commercial Profiling",
        owner="Security Team",
        created_date="2025-01-01",
        retention_period="3 years",
        expiry_date="2028-01-01",
        status="Active",
        source="Portal"
    )
    db.merge(rec)
    db.commit()
    db.close()

    mock_gemini_output = {
        "purpose_mismatch": True,
        "risk_level": "High",
        "ai_recommendation": "REVIEW",
        "explanation": "Commercial profiling exceeds account security consent."
    }

    with patch.object(GeminiAIProvider, "analyze", return_value=mock_gemini_output):
        response = client.post("/api/data/REC-AI-EP-01/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["record_id"] == "REC-AI-EP-01"
        assert data["analysis_mode"] == "ai_assisted"
        assert data["purpose_mismatch"] is True
        assert data["risk_level"] == "High"
        assert data["ai_recommendation"] == "REVIEW"
        assert "Commercial profiling" in data["explanation"]


def test_gemini_cache_avoids_duplicate_api_calls(monkeypatch):
    """Verify that identical governance evaluation queries hit cache and make only 1 HTTP call."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-cache")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.5-flash-lite")

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Audited compliant."
    })

    record_kwargs = {
        "category": "Customer",
        "sensitivity": "Low",
        "collection_purpose": "Billing Processing",
        "current_usage": "Invoice Settlement",
        "status": "Active",
        "expiry_date": "2028-01-01"
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        # First call: cache miss -> HTTP call executed
        res1 = GeminiAIProvider.analyze(**record_kwargs)
        assert res1 is not None
        assert mock_post.call_count == 1

        # Second call with identical input: cache hit -> no HTTP call
        res2 = GeminiAIProvider.analyze(**record_kwargs)
        assert res2 is not None
        assert mock_post.call_count == 1
        assert res1 == res2


def test_gemini_cache_varies_when_record_fields_differ(monkeypatch):
    """Verify that different input values generate distinct cache keys and separate calls."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-cache-diff")

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant."
    })

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        GeminiAIProvider.analyze(
            category="Customer",
            sensitivity="Low",
            collection_purpose="Support",
            current_usage="Ticket resolution",
            status="Active",
            expiry_date="2027-01-01"
        )
        assert mock_post.call_count == 1

        # Change current_usage to different purpose
        GeminiAIProvider.analyze(
            category="Customer",
            sensitivity="Low",
            collection_purpose="Support",
            current_usage="Cross-sell promotions",
            status="Active",
            expiry_date="2027-01-01"
        )
        assert mock_post.call_count == 2


def test_gemini_rate_limiter_throttles_and_falls_back(monkeypatch):
    """Verify that exceeding rate limiter quota falls back to rule-based analysis."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-limiter")
    monkeypatch.setattr("app.core.config.settings.GEMINI_RATE_LIMIT_RPM", 2)
    from app.services.ai_service import _rate_limiter
    _rate_limiter.rpm = 2
    _rate_limiter.interval = 60.0
    _rate_limiter.reset()

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant."
    })

    with patch("httpx.Client.post", return_value=mock_resp):
        # Call 1: passes
        r1 = AIService.analyze_record({
            "record_id": "REC-LIMIT-1",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Support",
            "current_usage": "Ticket inquiry",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })
        assert r1["analysis_mode"] == "ai_assisted"

        # Call 2: passes
        r2 = AIService.analyze_record({
            "record_id": "REC-LIMIT-2",
            "category": "Vendor",
            "sensitivity": "Medium",
            "collection_purpose": "Vendor invoicing",
            "current_usage": "Accounts payable",
            "status": "Active",
            "expiry_date": "2027-02-01"
        })
        assert r2["analysis_mode"] == "ai_assisted"

        # Mock rate limiter acquire to fail immediately (simulating quota exhaustion without waiting)
        with patch.object(_rate_limiter, "acquire", return_value=False):
            r3 = AIService.analyze_record({
                "record_id": "REC-LIMIT-3",
                "category": "Customer",
                "sensitivity": "High",
                "collection_purpose": "Order delivery",
                "current_usage": "Ad targeting",
                "status": "Active",
                "expiry_date": "2027-03-01"
            })
            # Must fall back cleanly to rule-based engine
            assert r3["analysis_mode"] == "rule_based"
            assert r3["purpose_mismatch"] is True


def test_gemini_retry_backoff_on_429_then_succeeds(monkeypatch):
    """Verify that HTTP 429 retries with backoff and parses Retry-After if provided."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-retry")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MAX_RETRIES", 2)

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}
    resp_429.text = '{"error": {"code": 429, "message": "RESOURCE_EXHAUSTED"}}'

    resp_200 = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant after retry."
    })

    with patch("httpx.Client.post", side_effect=[resp_429, resp_200]) as mock_post:
        with patch("time.sleep") as mock_sleep:
            result = GeminiAIProvider.analyze(
                category="General",
                sensitivity="Low",
                collection_purpose="Testing",
                current_usage="Testing usage",
                status="Active",
                expiry_date="2027-01-01"
            )
            assert result is not None
            assert result["explanation"] == "Compliant after retry."
            assert mock_post.call_count == 2
            mock_sleep.assert_called_with(0.01)


def test_gemini_governance_invariant_purpose_mismatch_cannot_recommend_keep(monkeypatch):
    """
    CRITICAL GOVERNANCE INVARIANT:
    If Gemini flags purpose_mismatch=True, the ai_recommendation CANNOT be KEEP.
    It must be overridden to REVIEW for human compliance intervention.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-gov")

    # Defective/inconsistent LLM output: mismatch is True but recommendation is KEEP
    inconsistent_llm_output = {
        "purpose_mismatch": True,
        "risk_level": "High",
        "ai_recommendation": "KEEP",
        "explanation": "Model mistakenly recommended KEEP despite divergence."
    }

    mock_resp = make_mock_gemini_response(inconsistent_llm_output)

    with patch("httpx.Client.post", return_value=mock_resp):
        result = AIService.analyze_record({
            "record_id": "REC-INVARIANT-01",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Order Fulfillment",
            "current_usage": "Commercial Data Resale",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert result["purpose_mismatch"] is True
        # Invariant enforced: KEEP was overridden to REVIEW
        assert result["ai_recommendation"] == "REVIEW"


def test_gemini_batch_analyze_database_efficiency(monkeypatch):
    """
    Verify batch_analyze_database uses structured batch analysis to evaluate
    records in chunks rather than firing sequential single requests.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-batch")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MODEL", "gemini-3.5-flash-lite")

    db = TestingSessionLocal()
    db.query(DataRecordModel).delete()
    db.commit()
    # Seed 3 records
    for i in range(3):
        rec = DataRecordModel(
            record_id=f"REC-BATCH-TEST-{i}",
            data_type="Customer Info",
            category="Customer",
            sensitivity="Medium",
            collection_purpose=f"Distinct purpose {i}",
            current_usage=f"Distinct usage {i}",
            owner="Ops",
            created_date="2025-01-01",
            retention_period="1 year",
            expiry_date="2026-01-01",
            status="Active",
            source="Web"
        )
        db.merge(rec)
    db.commit()

    # Create mock batch response
    batch_json = [
        {
            "index": 0,
            "purpose_mismatch": False,
            "risk_level": "Low",
            "ai_recommendation": "KEEP",
            "explanation": "Batch record 0 compliant."
        },
        {
            "index": 1,
            "purpose_mismatch": True,
            "risk_level": "High",
            "ai_recommendation": "REVIEW",
            "explanation": "Batch record 1 mismatch."
        },
        {
            "index": 2,
            "purpose_mismatch": False,
            "risk_level": "Low",
            "ai_recommendation": "KEEP",
            "explanation": "Batch record 2 compliant."
        }
    ]
    mock_batch_resp = make_mock_gemini_response(batch_json)

    with patch("httpx.Client.post", return_value=mock_batch_resp) as mock_post:
        res = AIService.batch_analyze_database(db=db, persist_results=False)
        assert res["total_analyzed"] >= 3
        # Should have made 1 batch request, not 3 separate requests
        assert mock_post.call_count == 1
    db.close()


# ==============================================================================
# Regression Tests for Gemini Optimization Fixes (Fix 2, Fix 3, Fix 4)
# ==============================================================================

def test_gemini_retry_after_429_consumes_rate_limit_permit(monkeypatch):
    """Fix 2: Verify every outbound request including retries acquires a rate-limit permit."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-retry-permit")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MAX_RETRIES", 2)
    from app.services.ai_service import _rate_limiter

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}
    resp_429.text = '{"error": {"code": 429, "message": "RESOURCE_EXHAUSTED"}}'

    resp_200 = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant after retry."
    })

    with patch.object(_rate_limiter, "acquire", wraps=_rate_limiter.acquire) as mock_acquire:
        with patch("httpx.Client.post", side_effect=[resp_429, resp_200]) as mock_post:
            with patch("time.sleep"):
                res = GeminiAIProvider.analyze(
                    category="Customer",
                    sensitivity="Low",
                    collection_purpose="Support Desk",
                    current_usage="Customer Ticket Resolution",
                    status="Active",
                    expiry_date="2027-01-01"
                )
                assert res is not None
                assert mock_post.call_count == 2
                # Every HTTP attempt must acquire a permit -> acquire called exactly 2 times
                assert mock_acquire.call_count == 2


def test_gemini_retry_stops_and_falls_back_when_rate_limit_cannot_be_acquired(monkeypatch):
    """Fix 2: When rate limiter refuses permit for a retry, stop retrying and fall back to rule-based."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-retry-limiter-fail")
    monkeypatch.setattr("app.core.config.settings.GEMINI_MAX_RETRIES", 2)
    from app.services.ai_service import _rate_limiter

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}
    resp_429.text = '{"error": {"code": 429, "message": "RESOURCE_EXHAUSTED"}}'

    # Permit 1 succeeds (for initial request), permit 2 fails (on retry)
    acquire_side_effects = [True, False]

    with patch.object(_rate_limiter, "acquire", side_effect=acquire_side_effects):
        with patch("httpx.Client.post", return_value=resp_429) as mock_post:
            with patch("time.sleep"):
                result = AIService.analyze_record({
                    "record_id": "REC-RETRY-FAIL-01",
                    "category": "Customer",
                    "sensitivity": "Low",
                    "collection_purpose": "Account Assistance",
                    "current_usage": "Customer Helpdesk Inquiries",
                    "status": "Active",
                    "expiry_date": "2027-01-01"
                })
                # Stopped after attempt 1 because permit for attempt 2 could not be acquired
                assert mock_post.call_count == 1
                # Falls back cleanly to deterministic rule-based engine
                assert result["analysis_mode"] == "rule_based"
                assert result["purpose_mismatch"] is False


def test_inflight_concurrent_requests_deduplicated_and_cleaned_up(monkeypatch):
    """Fix 3: Concurrent identical requests are deduplicated and inflight entries are cleaned up."""
    import concurrent.futures
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-inflight-clean")

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant concurrent."
    })

    call_count = 0
    tlock = threading.Lock()

    def slow_post(*args, **kwargs):
        nonlocal call_count
        with tlock:
            call_count += 1
        time.sleep(0.05)
        return mock_resp

    with patch("httpx.Client.post", side_effect=slow_post):
        # Fire 5 concurrent identical requests
        record_params = {
            "category": "Customer",
            "sensitivity": "Medium",
            "collection_purpose": "Identity Verification",
            "current_usage": "Passport Validation Check",
            "status": "Active",
            "expiry_date": "2028-01-01"
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(GeminiAIProvider.analyze, **record_params)
                for _ in range(5)
            ]
            results = [f.result() for f in futures]

        # All 5 requests returned the valid assessment
        for r in results:
            assert r is not None
            assert r["explanation"] == "Compliant concurrent."

        # Only 1 external HTTP request was made due to single-flight deduplication
        assert call_count == 1

        # In-flight entry was safely cleaned up and removed from memory
        assert GeminiAIProvider.get_inflight_count() == 0


def test_inflight_entries_stress_no_permanent_growth(monkeypatch):
    """Fix 3: Stress test over many distinct keys verifies zero permanent memory growth."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-stress")

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Compliant."
    })

    with patch("httpx.Client.post", return_value=mock_resp):
        for i in range(100):
            GeminiAIProvider.analyze(
                category="Customer",
                sensitivity="Low",
                collection_purpose=f"Unique purpose {i}",
                current_usage=f"Unique usage {i}",
                status="Active",
                expiry_date="2027-01-01"
            )

        # After all requests finish, inflight entries count MUST be 0
        assert GeminiAIProvider.get_inflight_count() == 0


def test_cache_prompt_version_invalidates_key():
    """Fix 4A: Changing prompt version produces a different cache key."""
    from app.services.ai_service import GeminiResponseCache, PROMPT_VERSION

    key_v1 = GeminiResponseCache.compute_key(
        model="gemini-3.5-flash-lite",
        category="Customer",
        sensitivity="Low",
        collection_purpose="Support",
        current_usage="Support",
        status="Active",
        expiry_date="2027-01-01",
        prompt_version="v1"
    )

    key_v2 = GeminiResponseCache.compute_key(
        model="gemini-3.5-flash-lite",
        category="Customer",
        sensitivity="Low",
        collection_purpose="Support",
        current_usage="Support",
        status="Active",
        expiry_date="2027-01-01",
        prompt_version="v2"
    )

    assert key_v1 != key_v2
    assert len(key_v1) == 64
    assert len(key_v2) == 64


def test_deterministic_identical_purpose_shortcut_skips_gemini(monkeypatch):
    """Fix 4B: Eligible records with identical purpose bypass Gemini API calls."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-shortcut")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", True)

    with patch("httpx.Client.post") as mock_post:
        # Eligible: Identical purpose and usage
        res = AIService.analyze_record({
            "record_id": "REC-SHORTCUT-01",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Order Fulfillment & Delivery",
            "current_usage": "Order Fulfillment & Delivery",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert not mock_post.called
        assert res["analysis_mode"] == "rule_based"
        assert res["purpose_mismatch"] is False
        assert res["ai_recommendation"] == "KEEP"


def test_deterministic_identical_purpose_shortcut_preserves_expiry_and_sensitivity_outcomes(monkeypatch):
    """Fix 4B: Different records with identical text preserve distinct lifecycle decisions."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-shortcut-outcomes")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", True)

    with patch("httpx.Client.post") as mock_post:
        # Record 1: Expired + High sensitivity -> ANONYMIZE
        r1 = AIService.analyze_record({
            "record_id": "REC-EXP-HIGH",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Billing Processing",
            "current_usage": "Billing Processing",
            "status": "Expired",
            "expiry_date": "2024-01-01"
        })
        assert r1["ai_recommendation"] == "ANONYMIZE"
        assert r1["risk_level"] == "High"

        # Record 2: Expired + Medium sensitivity -> REVIEW
        r2 = AIService.analyze_record({
            "record_id": "REC-EXP-MED",
            "category": "Customer",
            "sensitivity": "Medium",
            "collection_purpose": "Billing Processing",
            "current_usage": "Billing Processing",
            "status": "Expired",
            "expiry_date": "2024-01-01"
        })
        assert r2["ai_recommendation"] == "REVIEW"
        assert r2["risk_level"] == "High"

        # Record 3: Expiring Soon -> REVIEW
        r3 = AIService.analyze_record({
            "record_id": "REC-EXP-SOON",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Billing Processing",
            "current_usage": "Billing Processing",
            "status": "Expiring Soon",
            "expiry_date": "2026-11-01"
        })
        assert r3["ai_recommendation"] == "REVIEW"
        assert r3["risk_level"] == "Medium"

        assert not mock_post.called


def test_ineligible_records_with_different_purpose_still_query_gemini(monkeypatch):
    """Fix 4B: Records with differing purpose/usage are ineligible for shortcut and query Gemini."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-ineligible")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", True)

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": True,
        "risk_level": "High",
        "ai_recommendation": "REVIEW",
        "explanation": "Secondary monetization detected."
    })

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = AIService.analyze_record({
            "record_id": "REC-INELIGIBLE-01",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Account Administration",
            "current_usage": "Targeted Marketing Ads",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert mock_post.called
        assert res["analysis_mode"] == "ai_assisted"
        assert res["purpose_mismatch"] is True
        assert res["ai_recommendation"] == "REVIEW"


def test_disabling_skip_identical_purpose_queries_gemini_for_identical_text(monkeypatch):
    """Fix 4B: When GEMINI_SKIP_IDENTICAL_PURPOSE=False, identical text queries Gemini."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-skip-disabled")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Gemini confirmed compliant."
    })

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = AIService.analyze_record({
            "record_id": "REC-SKIP-OFF-01",
            "category": "Customer",
            "sensitivity": "Low",
            "collection_purpose": "Order Delivery",
            "current_usage": "Order Delivery",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert mock_post.called
        assert res["analysis_mode"] == "ai_assisted"
        assert res["explanation"] == "Gemini confirmed compliant."


def test_gemini_matching_purpose_queries_gemini_and_returns_ai_assisted(monkeypatch):
    """
    Verify matching-purpose records (e.g. CUS-1001) attempt Gemini when
    GEMINI_SKIP_IDENTICAL_PURPOSE=False and return analysis_mode='ai_assisted'.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-matching-assisted")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)

    mock_resp = make_mock_gemini_response({
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Gemini verified matching purpose is compliant."
    })

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = AIService.analyze_record({
            "record_id": "CUS-1001",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Order Processing & Delivery",
            "current_usage": "Order Processing & Delivery",
            "status": "Active",
            "expiry_date": "2027-01-01"
        })

        assert mock_post.called
        assert res["analysis_mode"] == "ai_assisted"
        assert res["purpose_mismatch"] is False
        assert res["ai_recommendation"] == "KEEP"
        assert res["explanation"] == "Gemini verified matching purpose is compliant."


def test_gemini_matching_purpose_falls_back_to_rule_based_on_api_error(monkeypatch):
    """
    Verify matching-purpose records fall back safely to rule-based engine and report
    analysis_mode='rule_based' when Gemini returns an HTTP error or times out.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-matching-fallback")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)

    mock_resp = make_mock_gemini_response({}, status_code=500)

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = AIService.analyze_record({
            "record_id": "CUS-1001",
            "category": "Customer",
            "sensitivity": "High",
            "collection_purpose": "Order Processing & Delivery",
            "current_usage": "Order Processing & Delivery",
            "status": "Expired",
            "expiry_date": "2025-01-15"
        })

        assert mock_post.called
        assert res["analysis_mode"] == "rule_based"
        assert res["purpose_mismatch"] is False
        assert res["risk_level"] in {"High", "Medium"}
        assert "PURPOSE COMPLIANT" in res["explanation"]


def test_gemini_matching_purpose_falls_back_to_rule_based_on_rate_limit(monkeypatch):
    """
    Verify matching-purpose records fall back safely to rule-based engine and report
    analysis_mode='rule_based' when process-local rate limiter refuses a request slot.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-matching-rate-limit")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)
    from app.services.ai_service import _rate_limiter

    with patch.object(_rate_limiter, "acquire", return_value=False):
        with patch("httpx.Client.post") as mock_post:
            res = AIService.analyze_record({
                "record_id": "CUS-1001",
                "category": "Customer",
                "sensitivity": "Low",
                "collection_purpose": "Order Processing",
                "current_usage": "Order Processing",
                "status": "Active",
                "expiry_date": "2027-01-01"
            })

            assert not mock_post.called
            assert res["analysis_mode"] == "rule_based"
            assert res["purpose_mismatch"] is False
            assert res["ai_recommendation"] == "KEEP"


def test_gemini_endpoint_analyze_matching_purpose_returns_ai_assisted(monkeypatch):
    """
    End-to-end endpoint test: POST /api/data/{record_id}/analyze for an identical-purpose
    record queries Gemini when GEMINI_SKIP_IDENTICAL_PURPOSE=False and returns ai_assisted.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-endpoint-matching")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)

    db = TestingSessionLocal()
    rec = DataRecordModel(
        record_id="TST-MATCH-01",
        data_type="Order Data",
        category="Customer",
        sensitivity="Medium",
        collection_purpose="Order Fulfillment",
        current_usage="Order Fulfillment",
        owner="Logistics",
        created_date="2025-01-01",
        retention_period="2 years",
        expiry_date="2027-01-01",
        status="Active",
        source="System"
    )
    db.merge(rec)
    db.commit()
    db.close()

    mock_gemini_output = {
        "purpose_mismatch": False,
        "risk_level": "Low",
        "ai_recommendation": "KEEP",
        "explanation": "Live Gemini confirmed operational usage matches stated collection purpose."
    }

    with patch.object(GeminiAIProvider, "analyze", return_value=mock_gemini_output) as mock_analyze:
        response = client.post("/api/data/TST-MATCH-01/analyze")
        assert response.status_code == 200
        data = response.json()
        assert mock_analyze.called
        assert data["record_id"] == "TST-MATCH-01"
        assert data["analysis_mode"] == "ai_assisted"
        assert data["purpose_mismatch"] is False
        assert data["risk_level"] == "Low"
        assert data["ai_recommendation"] == "KEEP"
        assert "Live Gemini confirmed" in data["explanation"]


def test_gemini_endpoint_analyze_matching_purpose_fallback_on_gemini_error(monkeypatch):
    """
    End-to-end endpoint test: POST /api/data/{record_id}/analyze gracefully returns HTTP 200
    with analysis_mode='rule_based' when Gemini provider fails for a matching-purpose record.
    """
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key-endpoint-matching-fail")
    monkeypatch.setattr("app.core.config.settings.GEMINI_SKIP_IDENTICAL_PURPOSE", False)

    db = TestingSessionLocal()
    rec = DataRecordModel(
        record_id="TST-MATCH-02",
        data_type="Order Data",
        category="Customer",
        sensitivity="Medium",
        collection_purpose="Order Fulfillment",
        current_usage="Order Fulfillment",
        owner="Logistics",
        created_date="2025-01-01",
        retention_period="2 years",
        expiry_date="2027-01-01",
        status="Active",
        source="System"
    )
    db.merge(rec)
    db.commit()
    db.close()

    with patch.object(GeminiAIProvider, "analyze", return_value=None):
        response = client.post("/api/data/TST-MATCH-02/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["record_id"] == "TST-MATCH-02"
        assert data["analysis_mode"] == "rule_based"
        assert data["purpose_mismatch"] is False
        assert data["ai_recommendation"] == "KEEP"