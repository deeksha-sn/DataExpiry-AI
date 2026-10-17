# DATAEXPIRY — Feature Status & Completeness Inventory

**Audit Classification Date:** October 16, 2026  
**Auditor:** Technical Audit Team  

### Classification Taxonomy:
- **COMPLETE:** Implementation exists and available code/test evidence demonstrates it works as intended.
- **PARTIAL:** Some functionality exists, but significant components or workflows are missing.
- **BROKEN:** Implementation exists but contains a defect, security failure, or runtime blocker.
- **NOT IMPLEMENTED:** Required functionality is completely absent in code.
- **UNVERIFIED:** Insufficient evidence or missing environment prevents verification.

---

## 1. Feature Status Summary Table

| ID | Feature Name | Layer | Status | Key Affected Files | Next Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FT-01** | System Health & Info | Full Stack | **COMPLETE** | `backend/app/api/routes.py`<br>`frontend/src/components/Layout.tsx` | Maintain. |
| **FT-02** | Enterprise Data Inventory API | Backend | **COMPLETE** | `backend/app/api/routes.py`<br>`backend/app/services/data_service.py` | Maintain. |
| **FT-03** | Data Inventory Catalog View | Frontend | **COMPLETE** | `frontend/src/pages/DataInventory.tsx` | Add record creation modal. |
| **FT-04** | Record Profile & Inspection View | Frontend | **COMPLETE** | `frontend/src/pages/RecordDetails.tsx` | Add action execution buttons. |
| **FT-05** | Semantic Purpose Mismatch Engine | Backend | **COMPLETE** | `backend/app/services/ai_service.py` | Maintain. |
| **FT-06** | Google Gemini LLM Integration | Backend | **COMPLETE** | `backend/app/services/ai_service.py` | Verify model identifier string compatibility. |
| **FT-07** | Interactive Purpose Sandbox | Full Stack | **COMPLETE** | `backend/app/api/routes.py`<br>`frontend/src/pages/PurposeMismatch.tsx` | Maintain. |
| **FT-08** | Batch AI Governance Audit | Full Stack | **COMPLETE** | `backend/app/api/routes.py`<br>`frontend/src/pages/AIInsights.tsx` | Maintain. |
| **FT-09** | Executive AI Governance Dashboard | Full Stack | **COMPLETE** | `backend/app/api/routes.py`<br>`frontend/src/pages/Dashboard.tsx` | Maintain. |
| **FT-10** | Retention Policy CRUD API | Backend | **COMPLETE** | `backend/app/api/policy_routes.py`<br>`backend/app/services/policy_service.py` | Maintain. |
| **FT-11** | Deterministic Policy Evaluation Engine | Backend | **COMPLETE** | `backend/app/services/policy_service.py` | Maintain. |
| **FT-12** | Policy Management UI | Frontend | **NOT IMPLEMENTED** | `frontend/src/pages/PolicyManagement.tsx`<br>`frontend/src/services/api.ts` | Build interactive policy management UI. |
| **FT-13** | Immutable Audit Log API | Backend | **COMPLETE** | `backend/app/api/audit_routes.py`<br>`backend/app/services/audit_service.py` | Maintain. |
| **FT-14** | Compliance Audit Trail UI | Frontend | **NOT IMPLEMENTED** | `frontend/src/pages/AuditTrail.tsx`<br>`frontend/src/services/api.ts` | Build interactive audit trail viewer UI. |
| **FT-15** | Lifecycle Action Execution | Backend | **PARTIAL** | `backend/app/services/lifecycle_service.py`<br>`backend/app/api/action_routes.py` | Implement real data masking/purging. |
| **FT-16** | Expiry Review Queue Workflow | Frontend | **PARTIAL** | `frontend/src/pages/ExpiryManagement.tsx` | Connect review queue to action execution API. |
| **FT-17** | Role-Based Access Control (RBAC) | Backend | **BROKEN** | `backend/app/core/security.py` | Remove default ADMIN bypass; add token auth. |
| **FT-18** | Automated Database Migrations | Backend | **NOT IMPLEMENTED** | `backend/app/database/session.py` | Initialize Alembic migrations environment. |

---

## 2. Detailed Feature Audit Records

### FT-01: System Health & Info Endpoint
- **Layer:** Backend & Frontend
- **Relevant Files:** `backend/app/api/routes.py` (lines 20–27), `frontend/src/components/Layout.tsx` (lines 20–30)
- **Current Implementation:** `GET /api/health` returns JSON `{"status": "ok", "service": "DATAEXPIRY API", "version": "1.0.0"}`. `Layout.tsx` polls health on mount and displays a green/red live indicator in the top navbar.
- **Dependencies:** FastAPI, Pydantic `HealthResponse`.
- **Known Defects:** None.
- **Evidence:** Verified in route code and frontend `Layout.tsx`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** None.

---

### FT-02: Enterprise Data Inventory API
- **Layer:** Backend
- **Relevant Files:** `backend/app/api/routes.py` (lines 29–76), `backend/app/services/data_service.py` (lines 7–57)
- **Current Implementation:** `GET /api/data` supports case-insensitive `category`, `status`, and `sensitivity` filters, with `limit` and `offset` pagination. `GET /api/data/{record_id}` supports lookup by string `record_id` (e.g. `CUS-1001`) or numerical integer ID. `POST /api/data` creates new records with duplicate `record_id` rejection.
- **Dependencies:** SQLAlchemy 2.0, SQLite/PostgreSQL, `DataRecordModel`, `DataRecordResponse`.
- **Known Defects:** No bulk CSV import endpoint.
- **Evidence:** Unit tests in `backend/tests/test_api.py` and `backend/tests/test_db.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Maintain.

---

### FT-03: Data Inventory Catalog View
- **Layer:** Frontend
- **Relevant Files:** `frontend/src/pages/DataInventory.tsx` (lines 1–41)
- **Current Implementation:** Rich, responsive catalog table with client-side text search across 6 fields (ID, type, category, purpose, usage, owner), multi-dropdown filtering by Category, Sensitivity, Status, Expiry Window, Purpose Mismatch, and Recommendation.
- **Dependencies:** `apiService.getDataRecords()`, React Router `Link`, Lucide icons.
- **Known Defects:** Missing a "Create New Record" UI modal/form to trigger `POST /api/data`.
- **Evidence:** Full table implementation present in `DataInventory.tsx`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Add a modal dialog with a form to create records.

---

### FT-04: Record Details Profile View
- **Layer:** Frontend
- **Relevant Files:** `frontend/src/pages/RecordDetails.tsx` (lines 1–164)
- **Current Implementation:** Inspects individual record metadata. Reads `?id=` query parameter or accepts manual search input. Displays sensitivity badges, collection purpose, current usage, and an "AI assessment" panel displaying recommendation, risk level, and explanation.
- **Dependencies:** `apiService.getDataRecord()`, `useSearchParams`.
- **Known Defects:** Has no action execution buttons. Users cannot execute `KEEP`, `REVIEW`, `ANONYMIZE`, or `DELETE` from this screen.
- **Evidence:** Code verified in `RecordDetails.tsx`.
- **Status:** **COMPLETE** (for viewing; action integration tracked under FT-15).
- **Recommended Next Action:** Add action execution buttons invoking the action API.

---

### FT-05: Semantic Purpose Mismatch Engine
- **Layer:** Backend
- **Relevant Files:** `backend/app/services/ai_service.py` (lines 1–650)
- **Current Implementation:**
  - Tokenization, stopword removal, and punctuation cleansing.
  - Multi-domain dictionary mapping (`DOMAIN_EQUIVALENTS` covering 9 operational categories: Operations, Support, Identity, Billing, Compliance, HR, Security, Loyalty, Analytics).
  - High-risk purpose creep detection (`HIGH_RISK_CREEP_SIGNALS` for Marketing, AI/ML Training, Data Monetization, Behavioral Profiling).
  - Jaccard token overlap for generic text comparison.
  - Generates clear, interpretable compliance explanation sentences.
- **Dependencies:** Python standard libraries (`re`, `json`, `logging`).
- **Known Defects:** None.
- **Evidence:** 771 lines of unit tests in `backend/tests/test_ai_service.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Maintain.

---

### FT-06: Google Gemini LLM Integration
- **Layer:** Backend
- **Relevant Files:** `backend/app/services/ai_service.py` (`GeminiAIProvider`, lines 118–382)
- **Current Implementation:** Dedicated REST client communicating with Google Generative Language REST API using `httpx`. Strict privacy boundary: only non-PII metadata is passed. Includes timeout handling (6.0s total, 3.0s connect), JSON schema validation of responses, and automatic fallback to rule-based engine on any error or timeout.
- **Dependencies:** `httpx`, `pydantic_settings`.
- **Known Defects / Risks:** Default model string in `.env.example` is `gemini-3.5-flash-lite`, which may not be a valid Google production model name (standard is `gemini-1.5-flash` or `gemini-2.0-flash`).
- **Evidence:** Code verified in `GeminiAIProvider` and mocked unit tests in `test_ai_service.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Update default model in `.env.example` to `gemini-1.5-flash` unless `gemini-3.5-flash-lite` is specifically provisioned.

---

### FT-07: Interactive Purpose Sandbox / Playground
- **Layer:** Full Stack
- **Relevant Files:** `backend/app/api/routes.py` (lines 128–146), `frontend/src/pages/PurposeMismatch.tsx` (lines 300–450)
- **Current Implementation:** Dedicated UI drawer allowing users to enter custom purpose and usage pairs, category, and sensitivity. Calls `POST /api/ai/check-mismatch` without mutating the database and renders immediate risk ratings and explanations.
- **Dependencies:** `apiService.checkPurposeMismatch()`.
- **Known Defects:** None.
- **Evidence:** Fully implemented in both frontend and backend.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Maintain.

---

### FT-08: Batch AI Governance Audit
- **Layer:** Full Stack
- **Relevant Files:** `backend/app/api/routes.py` (lines 82–92), `frontend/src/pages/PurposeMismatch.tsx` (lines 69–81), `frontend/src/pages/AIInsights.tsx` (lines 64–76)
- **Current Implementation:** "Run Global AI Audit" button on UI triggers `POST /api/ai/batch-analyze`. Backend scans all records in `data_records`, runs semantic evaluation, updates `purpose_mismatch`, `risk_level`, `ai_recommendation`, and `ai_explanation` columns, commits changes, and returns batch aggregate metrics.
- **Dependencies:** `AIService.batch_analyze_database()`.
- **Known Defects:** Large datasets may timeout on synchronous HTTP; lacks background Celery/rq job queue for enterprise scale.
- **Evidence:** Verified in route code and frontend handlers.
- **Status:** **COMPLETE** (for local/demo volume).
- **Recommended Next Action:** Add background task queue if record volume exceeds 1,000.

---

### FT-09: Executive AI Governance Dashboard
- **Layer:** Full Stack
- **Relevant Files:** `backend/app/api/routes.py` (lines 147–187), `frontend/src/pages/Dashboard.tsx` (lines 1–31)
- **Current Implementation:** Overview cards displaying total records, high-sensitivity assets, expiring soon, expired, purpose mismatches, pending reviews, and recommendation counts. Bar graphs illustrate breakdowns by sensitivity, category, lifecycle status, and expiry timeline buckets.
- **Dependencies:** `apiService.getDataRecords()`, `apiService.getAIGovernanceSummary()`.
- **Known Defects:** None.
- **Evidence:** Verified in `Dashboard.tsx`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Maintain.

---

### FT-10: Retention Policy CRUD API
- **Layer:** Backend
- **Relevant Files:** `backend/app/api/policy_routes.py` (lines 1–106), `backend/app/services/policy_service.py` (lines 245–345)
- **Current Implementation:** Full REST CRUD endpoints (`GET /api/policies`, `POST /api/policies`, `GET /api/policies/{id}`, `PUT /api/policies/{id}`, `DELETE /api/policies/{id}`). Includes soft deactivation (`is_active = False`), duration parsing ("2 years" -> 730 days), and role enforcement.
- **Dependencies:** `PolicyRuleModel`, `PolicyRuleCreate`, `PolicyRuleUpdate`, `PolicyRuleResponse`.
- **Known Defects:** None on backend.
- **Evidence:** Comprehensive test suite in `backend/tests/test_policy_engine.py` and `test_person4_api_integration.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Connect frontend UI.

---

### FT-11: Deterministic Policy Evaluation Engine
- **Layer:** Backend
- **Relevant Files:** `backend/app/services/policy_service.py` (lines 62–244), `backend/app/api/policy_routes.py` (lines 107–165)
- **Current Implementation:**
  - `evaluate_expiry()` computes status (`ACTIVE`, `EXPIRING_SOON`, `EXPIRED`) and delta days against an `as_of_date`.
  - Deterministic hierarchy:
    1. If `purpose_mismatch == True`: deterministic recommendation = `REVIEW` (strictly overrules AI `DELETE`/`KEEP`/`ANONYMIZE`).
    2. If status is `ACTIVE`: deterministic recommendation = `KEEP`.
    3. If status is `EXPIRING_SOON`: deterministic recommendation = `REVIEW`.
    4. If status is `EXPIRED`: deterministic recommendation = matched policy's `action_on_expiry`.
  - Batch evaluation endpoint `POST /api/policies/evaluate` returns aggregate summary and per-record evaluation items.
- **Dependencies:** `PolicyEvaluationSummary`, `PolicyEvaluationItem`.
- **Known Defects:** None.
- **Evidence:** Unit tests in `backend/tests/test_policy_engine.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Connect frontend UI.

---

### FT-12: Policy Management UI
- **Layer:** Frontend
- **Relevant Files:** `frontend/src/pages/PolicyManagement.tsx` (lines 1–47), `frontend/src/services/api.ts`
- **Current Implementation:** **Static placeholder banner.** Displays 3 feature cards ("Target Feature 1: Rule Builder", "Target Feature 2: Execution Triggers", "Target Feature 3: Compliance Overrides"). Zero API calls. `api.ts` has no policy methods.
- **Dependencies:** None currently wired.
- **Known Defects:** Complete absence of UI functionality.
- **Evidence:** Lines 24–43 in `PolicyManagement.tsx`.
- **Status:** **NOT IMPLEMENTED**
- **Recommended Next Action:** Implement functional policy table, policy creation form, active toggle, and batch evaluation trigger.

---

### FT-13: Immutable Audit Log API
- **Layer:** Backend
- **Relevant Files:** `backend/app/api/audit_routes.py` (lines 1–48), `backend/app/services/audit_service.py` (lines 1–76)
- **Current Implementation:** `GET /api/audit` retrieves audit events with optional filtering by `record_id`, `action`, `user`, with pagination (`limit`, `offset`). `GET /api/audit/{record_id}` returns chronological audit trail for a single record.
- **Dependencies:** `AuditLogModel`, `AuditLogResponse`.
- **Known Defects:** None.
- **Evidence:** Tests in `backend/tests/test_audit_service.py` and `test_person4_api_integration.py`.
- **Status:** **COMPLETE**
- **Recommended Next Action:** Connect frontend UI.

---

### FT-14: Compliance Audit Trail UI
- **Layer:** Frontend
- **Relevant Files:** `frontend/src/pages/AuditTrail.tsx` (lines 1–47), `frontend/src/services/api.ts`
- **Current Implementation:** **Static placeholder banner.** Displays 3 feature cards ("Target Feature 1: Lifecycle Event Logs", "Target Feature 2: Deletion Certificates", "Target Feature 3: Auditor Export"). Zero API calls. `api.ts` has no audit methods.
- **Dependencies:** None currently wired.
- **Known Defects:** Complete absence of UI functionality.
- **Evidence:** Lines 24–43 in `AuditTrail.tsx`.
- **Status:** **NOT IMPLEMENTED**
- **Recommended Next Action:** Implement functional audit trail table with action filtering, user filtering, and timeline drawer.

---

### FT-15: Lifecycle Action Execution Engine
- **Layer:** Backend
- **Relevant Files:** `backend/app/api/action_routes.py` (lines 1–47), `backend/app/services/lifecycle_service.py` (lines 1–150)
- **Current Implementation:** `POST /api/data/{record_id}/execute-action` takes `{"action": "...", "reason": "..."}`. Enforces RBAC permissions per role. Atomically updates record state and creates an immutable audit entry in the same transaction.
- **Dependencies:** `LifecycleActionResponse`, `AuditService`, `UserRole`.
- **Known Defects:**
  - **Simulated Deletion:** `DELETE` action only sets `deletion_status = "Deleted"` and `status = "Expired"`. The record row is not purged or deleted from SQL.
  - **Simulated Anonymization:** `ANONYMIZE` action only sets `anonymization_status = "Anonymized"` and `status = "Archived"`. No PII fields are masked or scrubbed.
  - Frontend has no action execution buttons in `RecordDetails.tsx`.
- **Evidence:** Comments and logic in `backend/app/services/lifecycle_service.py` (lines 90–106).
- **Status:** **PARTIAL**
- **Recommended Next Action:** Implement real data masking/purging or document the boundary as a metadata governance simulator. Connect frontend action triggers.

---

### FT-16: Expiry Review Queue Workflow
- **Layer:** Frontend
- **Relevant Files:** `frontend/src/pages/ExpiryManagement.tsx` (lines 1–23)
- **Current Implementation:** Renders 4 status lanes (Expiring Soon, Expired, Review Required, Completed). Includes a "Queue review" button.
- **Known Defects:** Clicking "Queue review" only updates local React component state array `queued: string[]`. Banner explicitly states: *"Actions on this page only create a temporary review queue in this browser session. No records are deleted, altered, or sent to a workflow API."*
- **Evidence:** Lines 15, 19, 20 in `ExpiryManagement.tsx`.
- **Status:** **PARTIAL**
- **Recommended Next Action:** Replace ephemeral React state with API calls to `POST /api/data/{record_id}/execute-action` with action `REVIEW`.

---

### FT-17: Role-Based Access Control (RBAC) Security
- **Layer:** Backend
- **Relevant Files:** `backend/app/core/security.py` (lines 1–55)
- **Current Implementation:** Role hierarchy defined (`ADMIN`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`, `AUDITOR`, `VIEWER`). `require_role()` dependency checks role against allowed list.
- **Known Defects:**
  - `get_current_user()` reads `X-User-Role` from request headers without authentication.
  - If `X-User-Role` header is omitted, defaults to `role = UserRole.ADMIN` and `user_id = "local_dev_user"`.
  - Zero authentication tokens (JWT), API keys, or session cookies are validated.
  - Anyone can impersonate any role by passing the header, or omit the header to obtain ADMIN rights.
- **Evidence:** Lines 23–38 in `security.py`.
- **Status:** **BROKEN**
- **Recommended Next Action:** Remove default ADMIN fallback. Enforce real authentication or implement an explicit development mode toggle with safe non-admin default (`VIEWER`).

---

### FT-18: Database Migrations
- **Layer:** Backend
- **Relevant Files:** `backend/app/database/session.py`
- **Current Implementation:** Raw `Base.metadata.create_all(bind=engine)` runs on server startup in `backend/app/main.py`.
- **Known Defects:** No Alembic configuration or migration history exists. Schema changes to existing SQLite databases fail or require deleting the `.db` file.
- **Evidence:** Absence of `alembic.ini` and `migrations/` directory.
- **Status:** **NOT IMPLEMENTED**
- **Recommended Next Action:** Initialize Alembic (`alembic init`) and generate initial migration script.
