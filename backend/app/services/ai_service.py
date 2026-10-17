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
import time
import random
import hashlib
import threading
from contextlib import contextmanager
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
DEFAULT_GEMINI_MODEL: str = "gemini-3.5-flash-lite"
PROMPT_VERSION: str = "v1"
GEMINI_API_ENDPOINT_TEMPLATE: str = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiRateLimiter:
    """
    Process-local sliding window rate limiter for Google Gemini API requests.
    Enforces a conservative requests-per-minute (RPM) limit (default: 10 RPM)
    to stay reliably within the free-tier quota (~15 RPM).

    PROCESS-LOCAL SCOPE NOTICE:
    This rate limiter coordinates requests within this single process/worker instance.
    It does not coordinate across multiple separate worker processes or horizontal instances.
    """
    def __init__(self, rpm_limit: int = 10):
        self.rpm_limit = max(1, rpm_limit)
        self.window_seconds = 60.0
        self.timestamps: List[float] = []
        self.lock = threading.Lock()

    def acquire(self, max_wait: float = 12.0) -> bool:
        """
        Attempts to acquire a request slot. Waits up to max_wait seconds if needed.
        Returns True if acquired, False if acquiring would exceed max_wait.
        """
        while True:
            with self.lock:
                now = time.time()
                cutoff = now - self.window_seconds
                self.timestamps = [t for t in self.timestamps if t > cutoff]

                if len(self.timestamps) < self.rpm_limit:
                    self.timestamps.append(now)
                    return True

                wait_time = (self.timestamps[0] + self.window_seconds) - now
                if wait_time <= 0:
                    self.timestamps.pop(0)
                    self.timestamps.append(now)
                    return True

                if wait_time > max_wait:
                    logger.warning(
                        f"Gemini rate limit slot unavailable (requires {wait_time:.1f}s wait > {max_wait:.1f}s max_wait). "
                        "Falling back to rule-based engine."
                    )
                    return False

            time.sleep(min(wait_time + 0.05, max_wait))

    def reset(self):
        with self.lock:
            self.timestamps.clear()


class GeminiResponseCache:
    """
    Bounded, thread-safe in-memory cache with TTL for Gemini governance assessments.
    Keys are SHA-256 hashes of normalized governance metadata and prompt version.
    Sensitive personal data, customer names, emails, and record_ids are NEVER stored in cache keys.
    """
    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.lock = threading.Lock()

    @staticmethod
    def compute_key(
        model: str,
        category: str,
        sensitivity: str,
        collection_purpose: str,
        current_usage: str,
        status: str,
        expiry_date: str,
        prompt_version: str = PROMPT_VERSION,
    ) -> str:
        raw = "|".join([
            (prompt_version or "").strip().lower(),
            (model or "").strip().lower(),
            (category or "").strip().lower(),
            (sensitivity or "").strip().lower(),
            (collection_purpose or "").strip().lower(),
            (current_usage or "").strip().lower(),
            (status or "").strip().lower(),
            (expiry_date or "").strip().lower(),
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            entry = self.cache.get(key)
            if not entry:
                return None
            timestamp, data = entry
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                return None
            return dict(data)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        with self.lock:
            if len(self.cache) >= self.max_entries and key not in self.cache:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
                del self.cache[oldest_key]
            self.cache[key] = (time.time(), dict(value))

    def clear(self):
        with self.lock:
            self.cache.clear()


_rate_limiter = GeminiRateLimiter(rpm_limit=getattr(settings, "GEMINI_RPM_LIMIT", 10))
_response_cache = GeminiResponseCache(
    ttl_seconds=getattr(settings, "GEMINI_CACHE_TTL_SECONDS", 3600),
    max_entries=getattr(settings, "GEMINI_CACHE_MAX_ENTRIES", 1000),
)


class _InflightEntry:
    def __init__(self):
        self.lock = threading.Lock()
        self.ref_count = 0


_inflight_entries: Dict[str, _InflightEntry] = {}
_inflight_master_lock = threading.Lock()


@contextmanager
def inflight_deduplication(key: str):
    """
    Reference-counted single-flight synchronization gate.
    Ensures identical concurrent requests share a lock to deduplicate work,
    and safely purges the entry from memory once all waiting/running callers exit.
    """
    with _inflight_master_lock:
        entry = _inflight_entries.get(key)
        if entry is None:
            entry = _InflightEntry()
            _inflight_entries[key] = entry
        entry.ref_count += 1

    try:
        with entry.lock:
            yield
    finally:
        with _inflight_master_lock:
            entry.ref_count -= 1
            if entry.ref_count <= 0:
                _inflight_entries.pop(key, None)


class GeminiAIProvider:
    """
    Dedicated Google Gemini REST API provider for semantic purpose mismatch evaluation.
    Communicates via httpx using Google's Generative Language REST API.
    Enforces strict privacy boundaries, timeout handling, process-local rate limiting (10 RPM default),
    request deduplication, in-memory caching, retry backoff with jitter, and schema validation.
    Returns None on any error or quota exhaustion to activate the deterministic rule-based fallback.
    """

    @classmethod
    def get_api_key(cls) -> str:
        """Retrieves configured Gemini API key, preferring GEMINI_API_KEY with AI_API_KEY fallback."""
        key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "AI_API_KEY", "")
        return key.strip() if key else ""

    @classmethod
    def get_model(cls) -> str:
        """Retrieves configured Gemini model name, defaulting to gemini-3.5-flash-lite."""
        model = getattr(settings, "GEMINI_MODEL", "").strip().strip('"').strip("'")
        if not model:
            model = DEFAULT_GEMINI_MODEL
        if model.startswith("models/"):
            model = model[len("models/"):]
        return model

    @classmethod
    def is_available(cls) -> bool:
        """Checks if a Gemini API key is configured."""
        return bool(cls.get_api_key())

    @classmethod
    def get_rate_limiter(cls) -> GeminiRateLimiter:
        return _rate_limiter

    @classmethod
    def get_cache(cls) -> GeminiResponseCache:
        return _response_cache

    @classmethod
    def get_inflight_count(cls) -> int:
        """Returns the number of active in-flight lock entries (for testing)."""
        with _inflight_master_lock:
            return len(_inflight_entries)

    @classmethod
    def reset_cache_and_limiter(cls):
        """Resets cache, rate limiter, and in-flight entries state (used in automated test suites)."""
        _response_cache.clear()
        _rate_limiter.reset()
        with _inflight_master_lock:
            _inflight_entries.clear()

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
            "   IMPORTANT: If purpose_mismatch is true, recommend 'REVIEW'. All recommendations are ADVISORY ONLY.\n"
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
    def build_batch_prompt(cls, items: List[Dict[str, Any]]) -> str:
        """
        Constructs a structured multi-record governance prompt to evaluate a batch
        in a single request, significantly reducing token consumption and API call volume.
        """
        prompt_parts = [
            "You are an enterprise data privacy and governance auditor specializing in GDPR, "
            "CCPA, and purpose limitation compliance.\n\n"
            "Evaluate whether active operational usage is compatible with stated collection purpose "
            "for each non-PII record item below.\n\n"
            "PRIVACY BOUNDARY: Only non-PII operational governance metadata is provided.\n\n"
            "METADATA RECORDS FOR AUDIT:\n"
        ]

        for idx, item in enumerate(items):
            prompt_parts.append(
                f"Item {idx}:\n"
                f"- Category: {item.get('category', 'General')}\n"
                f"- Sensitivity: {item.get('sensitivity', 'Medium')}\n"
                f"- Stated Collection Purpose: {item.get('collection_purpose', '')}\n"
                f"- Active Current Usage: {item.get('current_usage', '')}\n"
                f"- Retention Lifecycle Status: {item.get('status', 'Active')}\n"
                f"- Mandated Expiry Date: {item.get('expiry_date', 'N/A')}\n\n"
            )

        prompt_parts.append(
            "GOVERNANCE RULES:\n"
            "1. purpose_mismatch: true if usage introduces unconsented secondary use; false if compatible.\n"
            "2. risk_level: 'Critical', 'High', 'Medium', or 'Low'.\n"
            "3. ai_recommendation: 'KEEP', 'REVIEW', 'ANONYMIZE', or 'DELETE'. If purpose_mismatch is true, must be 'REVIEW'.\n"
            "4. explanation: concise 1-2 sentence advisory explanation.\n\n"
            "Return ONLY a valid JSON array of objects with the item index matching this schema:\n"
            "[\n"
            "  {\n"
            '    "index": 0,\n'
            '    "purpose_mismatch": true,\n'
            '    "risk_level": "High",\n'
            '    "ai_recommendation": "REVIEW",\n'
            '    "explanation": "concise explanation"\n'
            "  }\n"
            "]"
        )
        return "".join(prompt_parts)

    @classmethod
    def validate_assessment_dict(cls, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validates individual assessment dictionary against the strict governance schema.
        Enforces governance invariants (e.g. purpose_mismatch=True mandates REVIEW).
        """
        if not isinstance(parsed, dict):
            return None

        required_keys = {"purpose_mismatch", "risk_level", "ai_recommendation", "explanation"}
        if not required_keys.issubset(parsed.keys()):
            return None

        raw_mismatch = parsed.get("purpose_mismatch")
        if isinstance(raw_mismatch, bool):
            purpose_mismatch = raw_mismatch
        elif isinstance(raw_mismatch, str):
            if raw_mismatch.lower() == "true":
                purpose_mismatch = True
            elif raw_mismatch.lower() == "false":
                purpose_mismatch = False
            else:
                return None
        else:
            return None

        raw_risk = str(parsed.get("risk_level", "")).strip().title()
        if raw_risk not in VALID_RISK_LEVELS:
            return None

        raw_rec = str(parsed.get("ai_recommendation", "")).strip().upper()
        if raw_rec not in VALID_RECOMMENDATIONS:
            return None

        # Data governance safety invariant: Purpose mismatch MUST escalate to human review
        if purpose_mismatch and raw_rec == "KEEP":
            raw_rec = "REVIEW"

        raw_exp = str(parsed.get("explanation", "")).strip()
        if not raw_exp:
            return None

        return {
            "purpose_mismatch": purpose_mismatch,
            "risk_level": raw_risk,
            "ai_recommendation": raw_rec,
            "explanation": raw_exp,
        }

    @classmethod
    def parse_and_validate_response(cls, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parses raw LLM text into a validated dictionary.
        Returns None if parsing fails or values violate the required schema/types.
        """
        if not response_text or not response_text.strip():
            logger.warning("Invalid provider response: empty response text received.")
            return None

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

        assessment = cls.validate_assessment_dict(parsed)
        if not assessment:
            logger.warning("Invalid provider response: schema or domain validation failed.")
            return None

        return assessment

    @classmethod
    def parse_and_validate_batch_response(cls, response_text: str, expected_count: int) -> Optional[Dict[int, Dict[str, Any]]]:
        """
        Parses raw batch LLM text into a dictionary mapping index to assessment.
        """
        if not response_text or not response_text.strip():
            return None

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
        except Exception:
            return None

        if not isinstance(parsed, list):
            return None

        results_by_index: Dict[int, Dict[str, Any]] = {}
        for elem in parsed:
            if not isinstance(elem, dict) or "index" not in elem:
                continue
            idx = elem.get("index")
            validated = cls.validate_assessment_dict(elem)
            if validated and isinstance(idx, int) and 0 <= idx < expected_count:
                results_by_index[idx] = validated

        return results_by_index if len(results_by_index) > 0 else None

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
        Executes semantic analysis via Google Gemini REST API with:
        - In-memory caching with SHA-256 keys (avoids duplicate calls for identical inputs)
        - Single-flight deduplication across concurrent requests
        - Process-local sliding window rate limiting (10 RPM default for ~15 RPM quota)
        - Bounded exponential backoff with jitter on 429/503 errors and timeouts
        - Fail-safe fallback to deterministic rule-based analysis
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.debug("Gemini AI provider unavailable: no API key configured. Falling back to rule-based engine.")
            return None

        model = cls.get_model()
        cache_key = _response_cache.compute_key(
            model=model,
            category=category,
            sensitivity=sensitivity,
            collection_purpose=collection_purpose,
            current_usage=current_usage,
            status=status,
            expiry_date=expiry_date,
        )

        # 1. Quick cache check
        cached = _response_cache.get(cache_key)
        if cached is not None:
            logger.debug("Reusing cached Gemini governance assessment.")
            return cached

        # 2. Single-flight gate to prevent concurrent identical request bursts and clean up safely
        with inflight_deduplication(cache_key):
            # Re-check cache inside gate
            cached = _response_cache.get(cache_key)
            if cached is not None:
                logger.debug("Reusing cached Gemini governance assessment (single-flight deduplication).")
                return cached

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

            max_retries = getattr(settings, "GEMINI_MAX_RETRIES", 2)
            timeout_sec = getattr(settings, "GEMINI_TIMEOUT_SECONDS", 8.0)

            for attempt in range(max_retries + 1):
                # Rate limiter check for EVERY attempt, including retries
                if not _rate_limiter.acquire(max_wait=10.0):
                    logger.warning(
                        f"Gemini API rate limit reached on attempt {attempt + 1}/{max_retries + 1} "
                        "(process-local limiter). Falling back to rule-based engine."
                    )
                    return None

                try:
                    logger.info(
                        f"Initiating Gemini AI request (model: {model}, attempt {attempt + 1}/{max_retries + 1})..."
                    )
                    with httpx.Client(timeout=httpx.Timeout(timeout_sec, connect=3.0)) as client:
                        response = client.post(url, headers=headers, json=payload)

                    if response.status_code == 200:
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

                        # Cache valid assessment
                        _response_cache.set(cache_key, assessment)
                        logger.info("Successfully received and validated Gemini AI governance assessment.")
                        return assessment

                    # Handle 429 Rate Limit and 503 Unavailable with bounded backoff
                    if response.status_code in (429, 503) and attempt < max_retries:
                        retry_after = response.headers.get("Retry-After")
                        delay = None
                        if retry_after:
                            try:
                                delay = min(10.0, float(retry_after))
                            except ValueError:
                                pass
                        if delay is None:
                            delay = min(8.0, (1.5 ** attempt) * 2.0 + random.uniform(0.1, 0.5))

                        logger.warning(
                            f"Gemini API returned HTTP {response.status_code} (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        continue

                    # Non-retryable error (e.g. 400, 401, 403, 404) or retries exhausted
                    safe_body = (response.text or "").strip()
                    if api_key and api_key in safe_body:
                        safe_body = safe_body.replace(api_key, "[REDACTED]")
                    if len(safe_body) > 250:
                        safe_body = safe_body[:250] + "... (truncated)"
                    safe_body = safe_body.replace("\n", " ") if safe_body else "<empty response>"
                    logger.warning(
                        f"Gemini API request failed with HTTP status {response.status_code}: {safe_body}. "
                        "Falling back to rule-based engine."
                    )
                    return None

                except httpx.TimeoutException:
                    if attempt < max_retries:
                        delay = 1.0 + random.uniform(0.1, 0.5)
                        logger.warning(f"Gemini API request timed out. Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                        continue
                    logger.warning("Gemini API request timed out after retries. Falling back to rule-based engine.")
                    return None
                except httpx.HTTPError as e:
                    logger.warning(f"Gemini API HTTP communication error: {e}. Falling back to rule-based engine.")
                    return None
                except Exception as e:
                    logger.warning(f"Unexpected error querying Gemini API: {e}. Falling back to rule-based engine.")
                    return None

            return None

    @classmethod
    def batch_analyze(
        cls,
        items: List[Dict[str, Any]]
    ) -> Optional[Dict[int, Dict[str, Any]]]:
        """
        Executes a single structured batch evaluation request for multiple records.
        Reduces token consumption and API calls. Returns mapping of item index to assessment.
        """
        if not cls.is_available() or not items:
            return None

        api_key = cls.get_api_key()
        model = cls.get_model()
        url = GEMINI_API_ENDPOINT_TEMPLATE.format(model=model)
        prompt = cls.build_batch_prompt(items)

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        max_retries = getattr(settings, "GEMINI_MAX_RETRIES", 2)
        timeout_sec = getattr(settings, "GEMINI_TIMEOUT_SECONDS", 8.0) * 1.5

        for attempt in range(max_retries + 1):
            # Rate limiter check for EVERY attempt, including retries
            if not _rate_limiter.acquire(max_wait=10.0):
                logger.warning(
                    f"Gemini rate limit threshold reached on attempt {attempt + 1}/{max_retries + 1} for batch request. "
                    "Falling back to rule-based engine."
                )
                return None

            try:
                with httpx.Client(timeout=httpx.Timeout(timeout_sec, connect=3.0)) as client:
                    response = client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return None
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        return None
                    generated_text = parts[0].get("text", "")
                    parsed_batch = cls.parse_and_validate_batch_response(generated_text, len(items))
                    if not parsed_batch:
                        return None

                    # Cache each successfully assessed record
                    for idx, assessment in parsed_batch.items():
                        if idx < len(items):
                            it = items[idx]
                            ck = _response_cache.compute_key(
                                model=model,
                                category=it.get("category", ""),
                                sensitivity=it.get("sensitivity", ""),
                                collection_purpose=it.get("collection_purpose", ""),
                                current_usage=it.get("current_usage", ""),
                                status=it.get("status", ""),
                                expiry_date=it.get("expiry_date", ""),
                            )
                            _response_cache.set(ck, assessment)

                    return parsed_batch

                if response.status_code in (429, 503) and attempt < max_retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = None
                    if retry_after:
                        try:
                            delay = min(10.0, float(retry_after))
                        except ValueError:
                            pass
                    if delay is None:
                        delay = min(8.0, (1.5 ** attempt) * 2.0 + random.uniform(0.1, 0.5))
                    time.sleep(delay)
                    continue

                return None

            except (httpx.TimeoutException, httpx.HTTPError):
                if attempt < max_retries:
                    time.sleep(1.5 + random.uniform(0.1, 0.5))
                    continue
                return None
            except Exception:
                return None

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
        if not GeminiAIProvider.is_available():
            logger.debug("Gemini AI provider not configured. Using deterministic rule-based analysis.")
            return None

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

        # 1. Try AI provider if configured and record is not eligible for deterministic shortcut
        ai_result = None
        skip_identical = getattr(settings, "GEMINI_SKIP_IDENTICAL_PURPOSE", True)
        norm_purpose = cls.normalize_text(collection_purpose)
        norm_usage = cls.normalize_text(current_usage)
        is_identical_purpose = bool(norm_purpose and norm_usage and norm_purpose == norm_usage)

        if not (skip_identical and is_identical_purpose):
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
            mismatch = bool(ai_result.get("purpose_mismatch", False))
            rec = ai_result.get("ai_recommendation", "REVIEW")
            # Governance safety invariant: AI recommendation cannot be KEEP if purpose mismatch is flagged
            if mismatch and rec == "KEEP":
                rec = "REVIEW"
            return {
                "record_id": record_id,
                "category": category,
                "sensitivity": sensitivity,
                "collection_purpose": collection_purpose,
                "current_usage": current_usage,
                "purpose_mismatch": mismatch,
                "risk_level": ai_result.get("risk_level", "Medium"),
                "ai_recommendation": rec,
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
        Optimized for Gemini free tier (~15 RPM limit):
        - Leverages process-local cache to avoid redundant API calls
        - Batches un-cached records in structured chunks of 5 into single requests
        - Seamlessly falls back to deterministic rule-based analysis on rate limit or error
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

        # Pre-convert records to governance dicts
        rec_dicts: List[Dict[str, Any]] = []
        for rec in records:
            rec_dicts.append({
                "record_id": rec.record_id,
                "category": rec.category,
                "sensitivity": rec.sensitivity,
                "collection_purpose": rec.collection_purpose,
                "current_usage": rec.current_usage,
                "status": rec.status,
                "expiry_date": rec.expiry_date,
            })

        # If Gemini AI provider is available, batch evaluate items not yet cached
        if GeminiAIProvider.is_available() and rec_dicts:
            items_to_batch: List[Dict[str, Any]] = []
            skip_identical = getattr(settings, "GEMINI_SKIP_IDENTICAL_PURPOSE", True)
            for r_dict in rec_dicts:
                # If identical purpose shortcut is enabled, eligible records bypass external batch call
                if skip_identical:
                    np = cls.normalize_text(r_dict.get("collection_purpose", ""))
                    nu = cls.normalize_text(r_dict.get("current_usage", ""))
                    if np and nu and np == nu:
                        continue

                ck = _response_cache.compute_key(
                    model=GeminiAIProvider.get_model(),
                    category=r_dict["category"],
                    sensitivity=r_dict["sensitivity"],
                    collection_purpose=r_dict["collection_purpose"],
                    current_usage=r_dict["current_usage"],
                    status=r_dict["status"],
                    expiry_date=r_dict["expiry_date"],
                )
                if not _response_cache.get(ck):
                    items_to_batch.append(r_dict)

            # Send in chunks of 5 to respect token and payload constraints
            batch_size = 5
            for start_idx in range(0, len(items_to_batch), batch_size):
                chunk = items_to_batch[start_idx : start_idx + batch_size]
                GeminiAIProvider.batch_analyze(chunk)

        # Evaluate each record (retrieves cached assessment or uses rule-based engine)
        for i, rec in enumerate(records):
            analysis = cls.analyze_record(rec_dicts[i])
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
