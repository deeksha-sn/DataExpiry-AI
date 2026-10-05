"""
DATAEXPIRY — AI & Purpose Mismatch Engine
Assigned to: Team Member 2 (AI & Purpose Mismatch Lead)

Provides semantic purpose-mismatch detection, risk scoring, lifecycle recommendations
(KEEP, REVIEW, ANONYMIZE, DELETE), and natural language explanations.
Includes optional LLM provider mode with automatic, reliable rule-based fallback.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.data_record import DataRecordModel

logger = logging.getLogger(__name__)

# Stopwords for text normalization
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "for", "in", "on", "of", "to", "with",
    "by", "from", "at", "as", "is", "are", "be", "this", "that", "it",
    "data", "system", "management", "processing"
}

# Equivalent term clusters for semantic domain matching
DOMAIN_EQUIVALENTS: Dict[str, Set[str]] = {
    "OPERATIONS_FULFILLMENT": {
        "order", "orders", "processing", "fulfillment", "delivery", "dispatch",
        "shipping", "package", "tracking", "courier", "logistics", "warehouse"
    },
    "CUSTOMER_SUPPORT": {
        "support", "ticket", "tickets", "helpdesk", "resolution", "inquiry",
        "inquiries", "complaint", "assistance", "customer care", "help"
    },
    "ACCOUNT_IDENTITY": {
        "account", "profile", "registration", "credential", "auth", "login",
        "user data", "membership", "verification", "kyc", "identification",
        "identity", "passport", "license", "biometric"
    },
    "BILLING_FINANCE": {
        "billing", "payment", "invoice", "invoicing", "disbursement", "payroll",
        "salary", "transaction", "settlement", "tax", "accounting", "wire", "ledger"
    },
    "LEGAL_AUDIT_COMPLIANCE": {
        "tax audit", "audit", "compliance", "legal", "regulatory", "aml",
        "anti-money laundering", "fraud", "retention", "statutory", "governance"
    },
    "HR_EMPLOYMENT": {
        "payroll", "salary", "employment", "employee", "hr", "timecard",
        "benefits", "insurance", "recruitment", "interview", "hiring", "onboarding"
    },
    "SECURITY_ACCESS": {
        "physical security", "security access", "badge", "office access",
        "door access", "building access", "surveillance"
    },
    "LOYALTY_REWARDS": {
        "loyalty", "reward", "rewards", "points", "cashback", "tier", "club", "loyalty program"
    },
    "ANALYTICS_INTERNAL": {
        "analytics", "telemetry", "clickstream", "performance metrics",
        "monitoring", "ui optimization", "experience optimization"
    }
}

# Purpose creep clusters — secondary uses that trigger purpose mismatch unless explicitly consented
HIGH_RISK_CREEP_SIGNALS: Dict[str, Dict[str, Any]] = {
    "MARKETING_ADVERTISING": {
        "keywords": {
            "marketing", "advertisement", "advertising", "campaign", "campaigns",
            "promotion", "promotional", "sales targeting", "upselling", "telemarketing",
            "lead generation", "targeted marketing"
        },
        "description": "Secondary promotional/marketing campaigns without primary collection consent",
        "severity": "High"
    },
    "AI_ML_TRAINING": {
        "keywords": {
            "ai training", "model training", "machine learning", "llm", "ai resume screening",
            "algorithm training", "generative ai", "neural network training", "dataset training"
        },
        "description": "Repurposing operational or HR data for unapproved AI model training",
        "severity": "High"
    },
    "DATA_MONETIZATION": {
        "keywords": {
            "broker", "monetization", "reselling", "commercial sale", "third-party broker",
            "third party sharing", "external monetization", "data syndication"
        },
        "description": "Commercial data resale or unauthorized third-party broker transfer",
        "severity": "Critical"
    },
    "BEHAVIORAL_PROFILING": {
        "keywords": {
            "behavioral profiling", "user tracking", "cross-site tracking",
            "unauthorized risk modeling", "surveillance profiling"
        },
        "description": "Invasive behavioral tracking diverging from core transactional consent",
        "severity": "High"
    }
}

# ==============================================================================
# AI Provider Module: Google Gemini REST Client & Governance Validator
# ==============================================================================

VALID_RISK_LEVELS: Set[str] = {"Low", "Medium", "High", "Critical"}
VALID_RECOMMENDATIONS: Set[str] = {"KEEP", "REVIEW", "ANONYMIZE", "DELETE"}
DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash"
GEMINI_API_ENDPOINT_TEMPLATE: str = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiAIProvider:
    """
    Dedicated Google Gemini REST API provider for semantic purpose mismatch evaluation.
    Communicates via httpx using Google's Generative Language REST API.
    Enforces strict privacy boundaries, timeout handling, and schema validation.
    Returns None on any error to activate the deterministic rule-based fallback.
    """

    @classmethod
    def get_api_key(cls) -> str:
        """Retrieves configured Gemini API key, preferring GEMINI_API_KEY with AI_API_KEY fallback."""
        key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "AI_API_KEY", "")
        return key.strip() if key else ""

    @classmethod
    def get_model(cls) -> str:
        """Retrieves configured Gemini model name, defaulting to gemini-1.5-flash."""
        model = getattr(settings, "GEMINI_MODEL", "").strip()
        return model if model else DEFAULT_GEMINI_MODEL

    @classmethod
    def is_available(cls) -> bool:
        """Checks if a Gemini API key is configured."""
        return bool(cls.get_api_key())

    @classmethod
    def build_prompt(
        cls,
        category: str,
        sensitivity: str,
        collection_purpose: str,
        current_usage: str,
        status: str,
        expiry_date: str,
    ) -> str:
        """
        Constructs privacy-safe governance audit prompt for Gemini.

        =========================== PRIVACY BOUNDARY ===========================
        Under GDPR / CCPA data minimization principles:
        - ONLY non-PII operational governance metadata is included here:
          (category, sensitivity, collection_purpose, current_usage, status, expiry_date).
        - DO NOT SEND: customer names, email addresses, phone numbers,
          identity codes (record_id), passwords, financial details, or raw records.
        ========================================================================
        """
        return (
            "You are an enterprise data privacy and governance auditor specializing in GDPR, "
            "CCPA, and purpose limitation compliance.\n\n"
            "Evaluate whether the active operational usage of enterprise data is compatible "
            "with the stated purpose of collection.\n\n"
            "PRIVACY BOUNDARY: You are only provided non-PII governance metadata.\n\n"
            "METADATA FOR AUDIT:\n"
            f"- Data Category: {category}\n"
            f"- Data Sensitivity: {sensitivity}\n"
            f"- Stated Collection Purpose: {collection_purpose}\n"
            f"- Active Current Usage: {current_usage}\n"
            f"- Retention Lifecycle Status: {status}\n"
            f"- Mandated Expiry Date: {expiry_date}\n\n"
            "GOVERNANCE EVALUATION RULES:\n"
            "1. Purpose Mismatch: Set purpose_mismatch to true if active usage introduces secondary "
            "purposes (e.g. unconsented marketing, AI/ML model training, third-party broker monetization, "
            "cross-service profiling) not authorized by the stated collection purpose. Set to false if "
            "usage is operationally compatible or functionally equivalent.\n"
            "2. Risk Level: Set risk_level to 'Critical', 'High', 'Medium', or 'Low' considering data "
            "sensitivity, retention status (expired vs active), and degree of purpose divergence.\n"
            "3. Advisory Recommendation: Recommend 'KEEP', 'REVIEW', 'ANONYMIZE', or 'DELETE'.\n"
            "   IMPORTANT: This recommendation is ADVISORY ONLY. It does not execute actions or make binding "
            "governance decisions.\n"
            "4. Explanation: Provide a concise (1-2 sentences) natural language compliance explanation "
            "stating the rationale and that this is an advisory finding.\n\n"
            "Return ONLY a valid JSON object matching this schema exactly:\n"
            "{\n"
            '  "purpose_mismatch": true,\n'
            '  "risk_level": "High",\n'
            '  "ai_recommendation": "REVIEW",\n'
            '  "explanation": "concise advisory explanation"\n'
            "}"
        )

    @classmethod
    def parse_and_validate_response(cls, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parses raw LLM text into a validated dictionary.
        Returns None if parsing fails or values violate the required schema/types.
        """
        if not response_text or not response_text.strip():
            logger.warning("Invalid provider response: empty response text received.")
            return None

        # Clean potential markdown fences (e.g. ```json ... ```)
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned_text)
        except Exception as e:
            logger.warning(f"Invalid provider response: failed to parse JSON ({e}).")
            return None

        if not isinstance(parsed, dict):
            logger.warning("Invalid provider response: parsed JSON is not an object/dictionary.")
            return None

        # Check required fields
        required_keys = {"purpose_mismatch", "risk_level", "ai_recommendation", "explanation"}
        if not required_keys.issubset(parsed.keys()):
            missing = required_keys - set(parsed.keys())
            logger.warning(f"Invalid provider response: missing required fields {missing}.")
            return None

        # Validate purpose_mismatch boolean
        raw_mismatch = parsed.get("purpose_mismatch")
        if isinstance(raw_mismatch, bool):
            purpose_mismatch = raw_mismatch
        elif isinstance(raw_mismatch, str):
            if raw_mismatch.lower() == "true":
                purpose_mismatch = True
            elif raw_mismatch.lower() == "false":
                purpose_mismatch = False
            else:
                logger.warning(f"Invalid provider response: non-boolean purpose_mismatch '{raw_mismatch}'.")
                return None
        else:
            logger.warning(f"Invalid provider response: unexpected type for purpose_mismatch ({type(raw_mismatch)}).")
            return None

        # Validate risk_level (case-insensitive check against VALID_RISK_LEVELS)
        raw_risk = str(parsed.get("risk_level", "")).strip().title()
        if raw_risk not in VALID_RISK_LEVELS:
            logger.warning(f"Invalid provider response: invalid risk_level '{raw_risk}'.")
            return None

        # Validate ai_recommendation (case-insensitive check against VALID_RECOMMENDATIONS)
        raw_rec = str(parsed.get("ai_recommendation", "")).strip().upper()
        if raw_rec not in VALID_RECOMMENDATIONS:
            logger.warning(f"Invalid provider response: invalid ai_recommendation '{raw_rec}'.")
            return None

        # Validate explanation
        raw_exp = str(parsed.get("explanation", "")).strip()
        if not raw_exp:
            logger.warning("Invalid provider response: empty explanation.")
            return None

        return {
            "purpose_mismatch": purpose_mismatch,
            "risk_level": raw_risk,
            "ai_recommendation": raw_rec,
            "explanation": raw_exp,
        }

    @classmethod
    def analyze(
        cls,
        category: str,
        sensitivity: str,
        collection_purpose: str,
        current_usage: str,
        status: str,
        expiry_date: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes real Gemini REST API call using httpx.

        =========================== PRIVACY BOUNDARY ===========================
        Only non-PII operational governance metadata is accepted and passed.
        No customer names, emails, IDs, credentials, or document contents are ever transmitted.
        ========================================================================
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.debug("Gemini AI provider unavailable: no API key configured. Falling back to rule-based engine.")
            return None

        model = cls.get_model()
        url = GEMINI_API_ENDPOINT_TEMPLATE.format(model=model)
        prompt = cls.build_prompt(
            category=category,
            sensitivity=sensitivity,
            collection_purpose=collection_purpose,
            current_usage=current_usage,
            status=status,
            expiry_date=expiry_date,
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            logger.info(f"Initiating Gemini AI request (model: {model}) for semantic governance audit...")
            with httpx.Client(timeout=httpx.Timeout(6.0, connect=3.0)) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.warning(
                    f"Gemini API request failed with HTTP status {response.status_code}. "
                    "Falling back to rule-based engine."
                )
                return None

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("Gemini API response contained no candidates. Falling back to rule-based engine.")
                return None

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if not parts:
                logger.warning("Gemini API candidate contained no parts. Falling back to rule-based engine.")
                return None

            generated_text = parts[0].get("text", "")
            assessment = cls.parse_and_validate_response(generated_text)
            if not assessment:
                logger.warning("Gemini API response failed validation. Falling back to rule-based engine.")
                return None

            logger.info("Successfully received and validated Gemini AI governance assessment.")
            return assessment

        except httpx.TimeoutException:
            logger.warning("Gemini API request timed out. Falling back to rule-based engine.")
            return None
        except httpx.HTTPError as e:
            logger.warning(f"Gemini API HTTP communication error: {e}. Falling back to rule-based engine.")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error querying Gemini API: {e}. Falling back to rule-based engine.")
            return None


class AIService:
    """
    Core AI and purpose mismatch analysis service.
    Combines rule-based semantic NLP with optional LLM integration.
    """

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        """Lowercases and cleanses punctuation."""
        if not text:
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        return " ".join(cleaned.split())

    @classmethod
    def extract_keywords(cls, text: Optional[str]) -> Set[str]:
        """Extract meaningful semantic tokens from text."""
        normalized = cls.normalize_text(text)
        tokens = set(normalized.split())
        return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}

    @classmethod
    def detect_domains(cls, text: str) -> Set[str]:
        """Identifies standard operational domains matching the text."""
        norm_text = cls.normalize_text(text)
        tokens = cls.extract_keywords(text)
        matched_domains = set()

        for domain, keywords in DOMAIN_EQUIVALENTS.items():
            for kw in keywords:
                if " " in kw:
                    if kw in norm_text:
                        matched_domains.add(domain)
                        break
                elif kw in tokens:
                    matched_domains.add(domain)
                    break

        return matched_domains

    @classmethod
    def detect_creep_signals(cls, text: str) -> List[Tuple[str, str, str]]:
        """
        Scans text for secondary purpose creep patterns.
        Returns list of (creep_type, severity, description).
        """
        norm_text = cls.normalize_text(text)
        signals = []

        for creep_type, details in HIGH_RISK_CREEP_SIGNALS.items():
            for kw in details["keywords"]:
                if kw in norm_text:
                    signals.append((creep_type, details["severity"], details["description"]))
                    break

        return signals

    @classmethod
    def evaluate_purpose_compatibility(
        cls, collection_purpose: str, current_usage: str
    ) -> Tuple[bool, str, float, bool]:
        """
        Evaluates whether current_usage is compatible with collection_purpose.
        Returns (is_mismatch, detail_reason, divergence_score, is_ambiguous).
        Divergence score ranges from 0.0 (identical) to 1.0 (complete violation).
        """
        norm_purpose = cls.normalize_text(collection_purpose)
        norm_usage = cls.normalize_text(current_usage)

        # 1. Ambiguity / Insufficient Metadata check
        if len(norm_purpose) < 3 or len(norm_usage) < 3:
            return False, "Insufficient metadata provided for purpose comparison. Review required.", 0.5, True

        if norm_purpose in {"n a", "unknown", "none", "tbd", "test"} or norm_usage in {"n a", "unknown", "none", "tbd", "test"}:
            return False, "Ambiguous purpose or usage description. Manual governance review required.", 0.5, True

        # 2. Identical or near-identical text
        if norm_purpose == norm_usage:
            return False, "Operational usage exactly matches stated collection purpose.", 0.0, False

        purpose_tokens = cls.extract_keywords(collection_purpose)
        usage_tokens = cls.extract_keywords(current_usage)

        # 3. Check for unauthorized creep in usage that was NOT stated in purpose
        usage_creeps = cls.detect_creep_signals(current_usage)
        purpose_creeps = cls.detect_creep_signals(collection_purpose)
        purpose_creep_types = {c[0] for c in purpose_creeps}

        unauthorized_creeps = [c for c in usage_creeps if c[0] not in purpose_creep_types]

        if unauthorized_creeps:
            creep_type, severity, desc = unauthorized_creeps[0]
            reason = (
                f"Unauthorized purpose creep detected: active usage involves '{creep_type.replace('_', ' ').title()}' "
                f"({desc}), which was never authorized in stated collection purpose ('{collection_purpose}')."
            )
            score = 0.95 if severity == "Critical" else 0.85
            return True, reason, score, False

        # 4. Domain-level semantic alignment
        purpose_domains = cls.detect_domains(collection_purpose)
        usage_domains = cls.detect_domains(current_usage)

        # If both belong to the exact same functional domain(s), it is an equivalent wording
        common_domains = purpose_domains.intersection(usage_domains)
        if common_domains:
            domain_name = list(common_domains)[0].replace("_", " ").title()
            reason = (
                f"Semantically compatible: Usage aligns with collection intent under "
                f"the '{domain_name}' domain (Equivalent phrasing)."
            )
            return False, reason, 0.1, False

        # 5. Jaccard token overlap for general descriptions
        if purpose_tokens and usage_tokens:
            intersection = purpose_tokens.intersection(usage_tokens)
            union = purpose_tokens.union(usage_tokens)
            jaccard_sim = len(intersection) / len(union) if union else 0.0

            if jaccard_sim >= 0.20:
                return False, f"Compatible context: strong keyword overlap ({int(jaccard_sim*100)}%) between consent and usage.", 0.2, False
            elif jaccard_sim > 0.10:
                # Moderate overlap with different domains
                reason = (
                    f"Potential usage drift: usage has partial overlap but introduces secondary activities "
                    f"differing from primary collection purpose."
                )
                return True, reason, 0.65, False

        # 6. Completely disconnected domains without matching keywords
        reason = (
            f"Purpose mismatch: current usage '{current_usage}' diverges from original "
            f"collection purpose '{collection_purpose}' with no common operational domain."
        )
        return True, reason, 0.80, False

    @classmethod
    def calculate_risk_level(
        cls,
        purpose_mismatch: bool,
        status: str,
        sensitivity: str,
        divergence_score: float
    ) -> str:
        """
        Calculates risk rating (Critical, High, Medium, Low).
        """
        sens_upper = (sensitivity or "").strip().capitalize()
        status_upper = (status or "").strip().title()

        # Critical: Expired record with purpose violation OR high divergence on High sensitivity
        if status_upper == "Expired" and purpose_mismatch:
            return "Critical"
        if divergence_score >= 0.9 and sens_upper == "High":
            return "Critical"

        # High: Any purpose mismatch OR Expired record with High sensitivity
        if purpose_mismatch:
            return "High"
        if status_upper == "Expired" and sens_upper in {"High", "Medium"}:
            return "High"

        # Medium: Expired (Low sensitivity) OR Expiring Soon OR Ambiguous metadata
        if status_upper == "Expired":
            return "Medium"
        if status_upper == "Expiring Soon":
            return "Medium"
        if divergence_score >= 0.4:
            return "Medium"

        # Low: Active and compliant
        return "Low"

    @classmethod
    def determine_recommendation(
        cls,
        purpose_mismatch: bool,
        status: str,
        sensitivity: str,
        risk_level: str,
        is_ambiguous: bool = False
    ) -> str:
        """
        Determines automated lifecycle recommendation (KEEP, REVIEW, ANONYMIZE, DELETE).
        NOTE: Recommendations are advisory and do NOT override deterministic policy rules.
        """
        status_upper = (status or "").strip().title()
        sens_upper = (sensitivity or "").strip().capitalize()

        # Ambiguous metadata must always return REVIEW
        if is_ambiguous:
            return "REVIEW"

        # DELETE: Expired with purpose mismatch or critical risk
        if status_upper == "Expired" and purpose_mismatch:
            return "DELETE"
        if status_upper == "Expired" and risk_level == "Critical":
            return "DELETE"

        # ANONYMIZE: Expired High-sensitivity data or data kept for analytics
        if status_upper == "Expired" and sens_upper == "High" and not purpose_mismatch:
            return "ANONYMIZE"

        # REVIEW: Active record with purpose mismatch (needs human remediation) or Expired Low-risk
        if purpose_mismatch:
            return "REVIEW"
        if status_upper == "Expired":
            return "REVIEW"
        if status_upper == "Expiring Soon":
            return "REVIEW"

        # KEEP: Active, valid retention, no mismatch
        return "KEEP"

    @classmethod
    def generate_explanation(
        cls,
        record_id: str,
        purpose_mismatch: bool,
        detail_reason: str,
        status: str,
        sensitivity: str,
        expiry_date: str,
        recommendation: str,
        risk_level: str
    ) -> str:
        """Constructs an interpretable, natural language compliance explanation."""
        parts = []

        if purpose_mismatch:
            parts.append(f"[PURPOSE MISMATCH] {detail_reason}")
        else:
            parts.append(f"[PURPOSE COMPLIANT] {detail_reason}")

        if status == "Expired":
            parts.append(f"Record retention expired on {expiry_date}; retention period has lapsed.")
        elif status == "Expiring Soon":
            parts.append(f"Record is approaching scheduled expiry on {expiry_date}.")
        else:
            parts.append(f"Retention schedule is currently valid (expires {expiry_date}).")

        if sensitivity == "High":
            parts.append("High sensitivity data classification imposes stringent GDPR/CCPA governance controls.")

        if recommendation == "DELETE":
            parts.append("Recommendation: DELETE — Lawful basis has expired and active usage violates consent boundaries.")
        elif recommendation == "ANONYMIZE":
            parts.append("Recommendation: ANONYMIZE — De-identify personal identifiers while preserving aggregate analytical utility.")
        elif recommendation == "REVIEW":
            parts.append("Recommendation: REVIEW — Flagged for compliance review to rectify purpose creep or renew consent.")
        else:
            parts.append("Recommendation: KEEP — Operating within lawful retention schedule and stated collection purpose.")

        return " ".join(parts)

    @classmethod
    def _try_ai_provider(
        cls,
        record_id: str,
        category: str,
        sensitivity: str,
        collection_purpose: str,
        current_usage: str,
        status: str,
        expiry_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Executes semantic analysis via Google Gemini REST API if configured.

        =========================== PRIVACY BOUNDARY ===========================
        Only non-PII operational governance metadata (category, sensitivity,
        collection_purpose, current_usage, status, expiry_date) is passed to Gemini.
        record_id, customer names, emails, credentials, and document contents
        are strictly omitted from the external LLM prompt.
        ========================================================================

        FALLBACK BEHAVIOR:
        Returns None on any network failure, timeout, invalid schema, or missing API key,
        instantly falling back to the deterministic rule-based engine.
        """
        return GeminiAIProvider.analyze(
            category=category,
            sensitivity=sensitivity,
            collection_purpose=collection_purpose,
            current_usage=current_usage,
            status=status,
            expiry_date=expiry_date,
        )

    @classmethod
    def analyze_record(cls, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive purpose and lifecycle analysis for a single record dict.
        Returns a structured dictionary matching the required specification.
        """
        record_id = record_dict.get("record_id", "UNKNOWN")
        category = record_dict.get("category", "General")
        sensitivity = record_dict.get("sensitivity", "Medium")
        collection_purpose = record_dict.get("collection_purpose", "")
        current_usage = record_dict.get("current_usage", "")
        status = record_dict.get("status", "Active")
        expiry_date = record_dict.get("expiry_date", "N/A")

        # 1. Try AI provider if configured
        ai_result = cls._try_ai_provider(
            record_id=record_id,
            category=category,
            sensitivity=sensitivity,
            collection_purpose=collection_purpose,
            current_usage=current_usage,
            status=status,
            expiry_date=expiry_date
        )

        if ai_result:
            return {
                "record_id": record_id,
                "category": category,
                "sensitivity": sensitivity,
                "collection_purpose": collection_purpose,
                "current_usage": current_usage,
                "purpose_mismatch": bool(ai_result.get("purpose_mismatch", False)),
                "risk_level": ai_result.get("risk_level", "Medium"),
                "ai_recommendation": ai_result.get("ai_recommendation", "REVIEW"),
                "explanation": ai_result.get("explanation", ""),
                "analysis_mode": "ai_assisted"
            }

        # 2. Deterministic Rule-Based Analysis (Always available, robust fallback)
        is_mismatch, detail_reason, div_score, is_ambiguous = cls.evaluate_purpose_compatibility(
            collection_purpose=collection_purpose,
            current_usage=current_usage
        )

        risk_level = cls.calculate_risk_level(
            purpose_mismatch=is_mismatch,
            status=status,
            sensitivity=sensitivity,
            divergence_score=div_score
        )

        recommendation = cls.determine_recommendation(
            purpose_mismatch=is_mismatch,
            status=status,
            sensitivity=sensitivity,
            risk_level=risk_level,
            is_ambiguous=is_ambiguous
        )

        explanation = cls.generate_explanation(
            record_id=record_id,
            purpose_mismatch=is_mismatch,
            detail_reason=detail_reason,
            status=status,
            sensitivity=sensitivity,
            expiry_date=expiry_date,
            recommendation=recommendation,
            risk_level=risk_level
        )

        return {
            "record_id": record_id,
            "category": category,
            "sensitivity": sensitivity,
            "collection_purpose": collection_purpose,
            "current_usage": current_usage,
            "purpose_mismatch": is_mismatch,
            "risk_level": risk_level,
            "ai_recommendation": recommendation,
            "explanation": explanation,
            "analysis_mode": "rule_based"
        }

    @classmethod
    def batch_analyze_database(cls, db: Session, persist_results: bool = True) -> Dict[str, Any]:
        """
        Runs purpose mismatch detection across all records in the database.
        Optionally persists purpose_mismatch, risk_level, ai_recommendation,
        and ai_explanation directly to the database.
        """
        records: List[DataRecordModel] = db.query(DataRecordModel).all()
        results: List[Dict[str, Any]] = []

        total_analyzed = len(records)
        mismatches_count = 0
        review_count = 0
        keep_count = 0
        anonymize_count = 0
        delete_count = 0
        critical_risk_count = 0
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for rec in records:
            rec_dict = {
                "record_id": rec.record_id,
                "category": rec.category,
                "sensitivity": rec.sensitivity,
                "collection_purpose": rec.collection_purpose,
                "current_usage": rec.current_usage,
                "status": rec.status,
                "expiry_date": rec.expiry_date,
            }

            analysis = cls.analyze_record(rec_dict)
            results.append(analysis)

            # Update database record if requested
            if persist_results:
                setattr(rec, "purpose_mismatch", analysis["purpose_mismatch"])
                setattr(rec, "risk_level", analysis["risk_level"])
                setattr(rec, "ai_recommendation", analysis["ai_recommendation"])
                setattr(rec, "ai_explanation", analysis["explanation"])

            # Aggregate stats
            if analysis["purpose_mismatch"]:
                mismatches_count += 1
            if analysis["ai_recommendation"] == "REVIEW":
                review_count += 1
            elif analysis["ai_recommendation"] == "KEEP":
                keep_count += 1
            elif analysis["ai_recommendation"] == "ANONYMIZE":
                anonymize_count += 1
            elif analysis["ai_recommendation"] == "DELETE":
                delete_count += 1

            if analysis["risk_level"] == "Critical":
                critical_risk_count += 1
            elif analysis["risk_level"] == "High":
                high_risk_count += 1
            elif analysis["risk_level"] == "Medium":
                medium_risk_count += 1
            elif analysis["risk_level"] == "Low":
                low_risk_count += 1

        if persist_results and total_analyzed > 0:
            db.commit()

        return {
            "total_analyzed": total_analyzed,
            "potential_mismatches": mismatches_count,
            "records_requiring_review": review_count,
            "recommendations": {
                "KEEP": keep_count,
                "REVIEW": review_count,
                "ANONYMIZE": anonymize_count,
                "DELETE": delete_count
            },
            "risk_breakdown": {
                "Critical": critical_risk_count,
                "High": high_risk_count,
                "Medium": medium_risk_count,
                "Low": low_risk_count
            },
            "records": results
        }
