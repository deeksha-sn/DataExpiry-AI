# DATAEXPIRY — Engineering Handoff for ChatGPT

> **Notice for ChatGPT Pair-Programmer:**  
> This handoff contains the verified facts, architectural blueprint, code references, and immediate next steps for the DATAEXPIRY codebase in this workspace. You can proceed with implementation immediately using this document without re-auditing the entire repository.

---

## 1. Project Purpose & Target Users

**DATAEXPIRY** is an enterprise data lifecycle and purpose governance platform designed to discover, monitor, evaluate, and execute automated retention policies on enterprise data assets.

### Target Users:
- **Data Governance Leads & Administrators:** Configure retention policy rules per category, run compliance evaluations, and manage data lifecycles.
- **Data Privacy Officers (GDPR / CCPA):** Monitor secondary "purpose creep" (e.g. data gathered for Order Processing being repurposed for unconsented Marketing or AI training), review flagged records, and approve anonymization.
- **Compliance Auditors:** Inspect an immutable, cryptographic audit log of all data lifecycle transitions, reviews, and deletion proofs.

---

## 2. Confirmed Technology Stack & Workspace State

| Component | Technology | Version | Location |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI | `0.142.2` installed (`>=0.109.0` req) | `backend/app/main.py` |
| **Server Runtime** | Uvicorn | `0.54.0` installed (`[standard]>=0.27.0` req) | Port `8000` |
| **Validation** | Pydantic v2 | `2.13.5` installed (`>=2.6.0` req) | `backend/app/schemas/` |
| **ORM & Database** | SQLAlchemy 2.0 | SQLite (`sqlite:///./dataexpiry.db`) | `backend/app/database/` |
| **Test Framework** | Pytest + HTTPX | `pytest 9.1.1`, `httpx 0.28.1` | `backend/tests/` (9 test suites) |
| **AI Integration** | Google Gemini REST | `gemini-3.5-flash-lite` via `httpx` with rule fallback | `backend/app/services/ai_service.py` |
| **Frontend Framework**| React 18 | `18.2.0` with TypeScript `5.3.3` | `frontend/src/` |
| **Build & Dev Tool** | Vite | `5.1.4` (proxies `/api` -> `:8000`) | Port `5173` (`frontend/vite.config.ts`)|
| **Styling** | Tailwind CSS | `3.4.1` | `frontend/src/index.css` |
| **Routing** | React Router DOM | `6.22.2` (8 defined routes) | `frontend/src/App.tsx` |
| **Workspace / Git** | Local unversioned | **Not a git repository** (`DataExpiry-AI-main.zip` extract) | Root: `.` |

---

## 3. Important Directories & Critical Files Map

```
C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main\
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, Base.metadata.create_all, CORS, router mounting
│   │   ├── api/
│   │   │   ├── routes.py               # /api/health, /api/data (GET/POST), /api/ai/* (batch & sandbox)
│   │   │   ├── policy_routes.py        # /api/policies (CRUD), /api/policies/evaluate (batch & single)
│   │   │   ├── action_routes.py        # /api/data/{record_id}/execute-action
│   │   │   └── audit_routes.py         # /api/audit (GET all filterable), /api/audit/{record_id}
│   │   ├── core/
│   │   │   ├── config.py               # BaseSettings (DATABASE_URL, CORS_ORIGINS, GEMINI_API_KEY)
│   │   │   └── security.py             # UserRole enum, CurrentUser, get_current_user, require_role
│   │   ├── database/
│   │   │   └── session.py              # Engine, SessionLocal, Base, get_db dependency
│   │   ├── models/
│   │   │   ├── data_record.py          # DataRecordModel (`data_records` table)
│   │   │   ├── policy.py               # PolicyRuleModel (`retention_policies` table)
│   │   │   └── audit.py                # AuditLogModel (`audit_logs` table)
│   │   ├── schemas/
│   │   │   ├── data_record.py          # DataRecordBase/Create/Response, PurposeMismatchResult
│   │   │   ├── policy.py               # PolicyRuleCreate/Update/Response, PolicyEvaluationSummary
│   │   │   ├── audit.py                # AuditLogResponse, AuditFilterParams
│   │   │   └── action.py               # LifecycleActionRequest, LifecycleActionResponse
│   │   └── services/
│   │       ├── data_service.py         # DataRecordService: query filtering & creation
│   │       ├── ai_service.py           # AIService & GeminiAIProvider: NLP clusters & LLM client
│   │       ├── policy_service.py       # PolicyService: duration parser, expiry & policy evaluation
│   │       ├── lifecycle_service.py    # LifecycleService: execute_action & RBAC enforcement
│   │       └── audit_service.py        # AuditService: log_audit_event & get_audit_logs
│   ├── tests/                          # 9 complete pytest files covering all backend features
│   ├── seed_db.py                      # Initializes tables, seeds records.json & 3 demo policies
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # React Router routes (/ , /inventory, /records, /expiry, etc.)
│   │   ├── components/
│   │   │   ├── Layout.tsx              # App chrome with dark mode and backend connection badge
│   │   │   └── Navigation.tsx          # Sidebar with NavLinks
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx           # WORKING: Metrics, distribution bars, KPI tiles
│   │   │   ├── DataInventory.tsx       # WORKING: Catalog table with multi-dropdown search/filtering
│   │   │   ├── RecordDetails.tsx       # WORKING: Profile lookup by ID; displays metadata & AI assess
│   │   │   ├── ExpiryManagement.tsx    # PARTIAL: 4 status lanes; "Queue review" is local state only
│   │   │   ├── PurposeMismatch.tsx     # WORKING: Creep monitor, single/batch analysis, sandbox
│   │   │   ├── AIInsights.tsx          # WORKING: Action tabs (KEEP/REVIEW/ANONYMIZE/DELETE), modal
│   │   │   ├── PolicyManagement.tsx    # PLACEHOLDER: Static banner; needs full API integration
│   │   │   └── AuditTrail.tsx          # PLACEHOLDER: Static banner; needs full API integration
│   │   ├── services/
│   │   │   └── api.ts                  # Centralized fetch class (NEEDS policy, audit, action methods)
│   │   └── types/
│   │       └── index.ts                # TypeScript interfaces (NEEDS policy, audit, action types)
│   ├── package.json
│   └── vite.config.ts                  # Proxies /api -> http://localhost:8000
│
├── data/
│   └── synthetic/
│       ├── records.json                # 20 initial synthetic data records
│       └── generator.py                # CLI script to generate 100+ synthetic records
└── docs/
    └── ARCHITECTURE.md                 # Initial foundation documentation
```

---

## 4. Key Classes, Functions, and API Routes

### Backend Models & Schemas
- `DataRecordModel` (`backend/app/models/data_record.py`): Table `data_records`. Fields: `record_id`, `data_type`, `category`, `sensitivity`, `collection_purpose`, `current_usage`, `owner`, `created_date`, `retention_period`, `expiry_date`, `status`, `last_accessed`, `source`, `purpose_mismatch`, `risk_level`, `ai_recommendation`, `ai_explanation`, `policy_rule`, `review_status`, `anonymization_status`, `deletion_status`.
- `PolicyRuleModel` (`backend/app/models/policy.py`): Table `retention_policies`. Fields: `rule_code`, `name`, `category`, `retention_period`, `retention_days`, `action_on_expiry` (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`), `description`, `is_active`.
- `AuditLogModel` (`backend/app/models/audit.py`): Table `audit_logs`. Fields: `audit_id`, `record_id`, `action`, `previous_status`, `new_status`, `user`, `timestamp`, `reason`, `ai_recommendation`, `policy_rule`, `created_at`.

### Core Services
- `AIService.evaluate_purpose_compatibility(purpose, usage)`: Evaluates semantic drift using dictionary clusters (`DOMAIN_EQUIVALENTS`, `HIGH_RISK_CREEP_SIGNALS`) and Jaccard token overlap.
- `GeminiAIProvider.analyze(...)`: Calls Google Generative Language REST API (`POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`) with non-PII metadata. Times out after 6.0s and returns `None` to seamlessly trigger the rule-based fallback.
- `PolicyService.evaluate_expiry(expiry_date_str, as_of_date, expiring_soon_days)`: Returns `(status, delta_days)`.
- `PolicyService.evaluate_record(db, record, as_of_date, expiring_soon_days)`: Applies deterministic governance hierarchy:
  - Purpose Mismatch == True -> `REVIEW` (overrules AI recommendation).
  - Expiry Status == ACTIVE -> `KEEP`.
  - Expiry Status == EXPIRING_SOON -> `REVIEW`.
  - Expiry Status == EXPIRED -> matched policy's `action_on_expiry`.
- `LifecycleService.execute_action(db, record_id, action, user, role, reason)`: Enforces RBAC permissions per role and atomically records an immutable audit log entry in the same transaction.

### Critical Routes
- `GET /api/data`: Query filtered data records.
- `GET /api/data/{record_id}`: Single record lookup.
- `POST /api/ai/batch-analyze`: Batch evaluates all records in database and updates AI fields.
- `POST /api/ai/check-mismatch`: Interactive playground for purpose compatibility testing.
- `GET /api/policies` / `POST /api/policies`: Policy CRUD.
- `POST /api/policies/evaluate`: Deterministic batch evaluation against active policies.
- `POST /api/data/{record_id}/execute-action`: Execute `KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`.
- `GET /api/audit`: Query immutable audit trail logs.

---

## 5. Working vs. Incomplete Features

### Working Features:
- System healthcheck and connection monitor (`GET /api/health`, `Layout.tsx`).
- Data record CRUD and query filtering in backend and `DataInventory.tsx`.
- Record profile inspection in `RecordDetails.tsx`.
- Purpose mismatch detection, keyword extraction, and creep detection in `AIService`.
- Google Gemini REST provider with automatic rule-based fallback.
- Batch AI analysis trigger in `AIInsights.tsx` and `PurposeMismatch.tsx`.
- Interactive purpose-usage sandbox in `PurposeMismatch.tsx`.
- Retention policy CRUD and deterministic evaluation engine in backend.
- Immutable audit log recording and query service in backend.

### Incomplete Features & Disconnects:
1. **Policy Management UI (`PolicyManagement.tsx`):** Pure static placeholder banner. Needs full table view, creation modal, and evaluation trigger wired to `/api/policies`.
2. **Audit Trail UI (`AuditTrail.tsx`):** Pure static placeholder banner. Needs full table view and timeline drawer wired to `/api/audit`.
3. **Frontend API Service (`api.ts`):** Has zero methods for policies, audit logs, or lifecycle actions.
4. **Action Execution Trigger:** `ExpiryManagement.tsx` only updates local React state array `queued`. `RecordDetails.tsx` has no action execution buttons. Neither calls `POST /api/data/{record_id}/execute-action`.
5. **Simulated Deletion & Anonymization:** `LifecycleService.execute_action` sets status strings (`deletion_status = "Deleted"`, `anonymization_status = "Anonymized"`) but does not purge rows or mask sensitive fields.

---

## 6. Confirmed Bugs & Security Issues

1. **[CRITICAL] Insecure RBAC Default to ADMIN:**
   - In `backend/app/core/security.py` (lines 23–38), `get_current_user` falls back to `UserRole.ADMIN` and `user_id = "local_dev_user"` whenever `X-User-Role` header is omitted. Anyone can bypass authorization controls or elevate privileges.
2. **[HIGH] Lack of Client Authentication:**
   - RBAC relies solely on unauthenticated HTTP headers (`X-User-Role`, `X-User-Id`). No JWT, OAuth2, session cookies, or API token validation exists.
3. **[HIGH] Simulated Deletion Compliance Hazard:**
   - Records marked "Deleted" are retained in SQLite in plaintext and continue to appear in standard catalog queries.
4. **[MEDIUM] Missing Database Migration Framework:**
   - Relying on `Base.metadata.create_all` prevents safe schema migrations.
5. **[LOW] Gemini Model Name Validation:**
   - Model `gemini-3.5-flash-lite` in `.env.example` may not match Google's active API endpoints; verify or use `gemini-1.5-flash`.

---

## 7. Setup & Run Instructions (Verified)

### Backend Setup:
```bash
cd backend

# 1. Create and activate virtual environment
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file from example
copy .env.example .env

# 4. Initialize database and seed synthetic records
python seed_db.py

# 5. Run tests to verify
pytest

# 6. Start backend development server
uvicorn app.main:app --reload --port 8000
```
Swagger UI will be available at: `http://localhost:8000/docs`

### Frontend Setup:
```bash
cd frontend

# 1. Install node dependencies
npm install

# 2. Run TypeScript check
npm run lint

# 3. Start Vite development server
npm run dev
```
Web Application will run at: `http://localhost:5173` (proxies `/api` requests to `:8000`).

---

## 8. Required Configuration Environment Variables

Configured in `backend/.env` (parsed by `backend/app/core/config.py`):

| Variable Name | Purpose | Default / Example Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection URL | `sqlite:///./dataexpiry.db` |
| `HOST` | Backend server bind address | `0.0.0.0` |
| `PORT` | Backend server port | `8000` |
| `ENVIRONMENT` | Runtime environment mode | `development` |
| `CORS_ORIGINS` | Allowed CORS origins JSON list | `["http://localhost:5173", "http://127.0.0.1:5173"]` |
| `GEMINI_API_KEY` | Google Generative Language API key | `""` (Optional; runs rule-based engine if empty) |
| `GEMINI_MODEL` | Gemini model name | `gemini-3.5-flash-lite` or `gemini-1.5-flash` |
| `AI_API_KEY` | Secondary fallback key alias | `""` |

*Note: All secret keys must remain in `.env` and are strictly excluded by `.gitignore`.*

---

## 9. Next 3 Recommended Tasks for ChatGPT

### Task 1 (Immediate Next Task): Wire Frontend API Service & Types
- **Goal:** Add TypeScript interfaces and API methods in `frontend/src/types/index.ts` and `frontend/src/services/api.ts` for Policies, Audit, and Actions.
- **Acceptance Criteria:**
  - `PolicyRule`, `PolicyRuleCreateInput`, `PolicyEvaluationSummary`, `AuditLogEntry`, `LifecycleActionRequest`, `LifecycleActionResponse` interfaces exported in `types/index.ts`.
  - `apiService` provides `getPolicies()`, `createPolicy()`, `evaluatePolicies()`, `getAuditLogs()`, `executeLifecycleAction()`.
  - `npm run lint` passes with 0 errors.

### Task 2: Build Interactive Policy Management Page (`PolicyManagement.tsx`)
- **Goal:** Replace the static mockup with a functional table of policies, "Add Policy" modal, active toggle, and "Run Policy Evaluation" summary view.
- **Acceptance Criteria:**
  - Loads real policies from `GET /api/policies`.
  - Allows creating new policies via `POST /api/policies`.
  - Allows running batch evaluation via `POST /api/policies/evaluate` and renders results.

### Task 3: Build Compliance Audit Trail Page (`AuditTrail.tsx`)
- **Goal:** Replace the static mockup with an immutable audit log viewer.
- **Acceptance Criteria:**
  - Loads audit logs from `GET /api/audit`.
  - Provides search filters by Action (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`), User, and Record ID.
  - Displays chronological timestamp, actor, status delta, and compliance justification.

---

## 10. Engineering Constraints to Respect

1. **Do Not Break AI Rule-Based Fallback:** `AIService` must always function reliably even when `GEMINI_API_KEY` is empty, expired, or invalid.
2. **Preserve Deterministic Policy Hierarchy:** In `PolicyService.evaluate_record`, `purpose_mismatch == True` must strictly mandate `REVIEW` regardless of any advisory LLM recommendation.
3. **Atomic Audit Transactions:** Any lifecycle action mutation must record its corresponding `AuditLogModel` entry within the same database transaction (`db.commit()` only after both succeed).
4. **No Destructive Database Changes:** SQLite development data must not be wiped; use non-destructive schema extensions or migrations.
5. **Header-Based RBAC Header Preservation:** While hardening security, ensure the test suite's `X-User-Role` and `X-User-Id` header conventions continue to be supported for integration testing.
