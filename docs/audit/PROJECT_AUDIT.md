# DATAEXPIRY — Comprehensive Engineering & Architectural Audit

**Audit Date:** October 16, 2026  
**Auditor Roles:** Senior Software Architect, Staff Engineer, QA Engineer, Technical Auditor  
**Audit Scope:** Full codebase inspection (`backend/`, `frontend/`, `data/`, `docs/`, root config)  
**Audit Mode:** READ-ONLY AUDIT (Zero code modifications, package installations, or destructive operations performed)

---

## 1. Executive Summary

**DATAEXPIRY** is an enterprise data lifecycle and purpose governance platform designed to help organizations discover, monitor, evaluate, and execute automated lifecycle policies on enterprise data assets. It targets enterprise privacy officers, data governance teams, compliance auditors, and administrators managing compliance under regulations such as GDPR and CCPA.

### High-Level Status
The project represents a multi-person collaborative initiative with foundational architecture and substantial backend logic already implemented. However, the system is in an **asymmetrically finished state**:
- **Backend Foundation & AI Engine:** Highly mature (~85% complete). Complete data catalog service, advanced semantic purpose-mismatch engine with keyword extraction and NLP clustering, Google Gemini REST integration with automated rule-based fallback, comprehensive deterministic policy engine, and atomic audit logging. 9 unit and integration test suites are present in `backend/tests/`.
- **Frontend Application:** Partially implemented (~50% complete). Rich dashboard, data catalog table with deep search/filtering, record profile viewer, and dedicated AI insights and purpose mismatch pages are operational. However, **Policy Management** (`PolicyManagement.tsx`) and **Compliance Audit Trail** (`AuditTrail.tsx`) are **static placeholder mockups** containing promotional banners rather than functional user interfaces.
- **Integration Disconnects:** The frontend API service (`frontend/src/services/api.ts`) contains zero API methods for policy CRUD, policy evaluation, audit logging, or action execution. Lifecycle actions (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`) cannot be triggered from the frontend.
- **Security Posture:** Critical vulnerability detected. Role-Based Access Control (RBAC) relies on unauthenticated HTTP request headers (`X-User-Role`, `X-User-Id`) and insecurely defaults to `ADMIN` privileges if the headers are absent.
- **Execution & Test Health:** The workspace is an unversioned ZIP extract lacking installed dependencies. No Python virtual environment exists (`ModuleNotFoundError: No module named 'sqlalchemy'`), and frontend `node_modules` is missing (`tsc is not recognized`), preventing test execution and build verification in the uninitialized environment.

---

## 2. Project Identity & Technology Stack

| Attribute | Verified Setting |
| :--- | :--- |
| **Workspace Root** | `C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main` |
| **Project Name** | `DATAEXPIRY` (Repository folder: `DataExpiry-AI-main`) |
| **Project Archetype** | Multi-tier Web Application (Monorepo with decoupled `backend/` and `frontend/`) |
| **Repository State** | Uncommitted local workspace. **Not a git repository** (`fatal: not a git repository`). Extracted from GitHub archive `DataExpiry-AI-main.zip`. |
| **Backend Framework** | Python 3.10+ (Host: Python 3.13.2) with **FastAPI** (`0.142.2` installed, `>=0.109.0` specified) |
| **API Server** | **Uvicorn** (`0.54.0` installed, `[standard]>=0.27.0` specified) |
| **Data Validation** | **Pydantic v2** (`2.13.5` installed, `>=2.6.0` specified) & `pydantic-settings` (`>=2.1.0`) |
| **ORM & Database** | **SQLAlchemy 2.0** (`>=2.0.25` specified). Default SQLite (`sqlite:///./dataexpiry.db`), PostgreSQL ready. |
| **Backend Testing** | **Pytest** (`9.1.1` installed, `>=8.0.0` specified), **HTTPX** (`0.28.1` installed, `>=0.26.0` specified) |
| **AI / LLM Integration** | **Google Gemini REST API** (`gemini-3.5-flash-lite`) via `httpx` with rule-based semantic NLP fallback |
| **Frontend Framework** | **React 18** (`^18.2.0`) with **TypeScript** (`^5.3.3`) |
| **Frontend Build Tool** | **Vite** (`^5.1.4`) with `@vitejs/plugin-react` (`^4.2.1`) |
| **Frontend Styling** | **Tailwind CSS** (`^3.4.1`), **PostCSS** (`^8.4.35`), **Autoprefixer** (`^10.4.18`) |
| **Frontend Routing** | **React Router DOM v6** (`^6.22.2`) |
| **Frontend Icons** | **Lucide React** (`^0.344.0`) |
| **HTTP Client** | Native browser `fetch` via centralized service (`frontend/src/services/api.ts`) |

---

## 3. Git & Workspace State

- **Git Status:** [VERIFIED FACT] The directory is not initialized as a Git repository. Running `git status`, `git branch -a`, `git remote -v`, and `git log` returns:
  `fatal: not a git repository (or any of the parent directories): .git`.
- **Origin Analysis:** The directory name `DataExpiry-AI-main` confirms this workspace was extracted from a GitHub repository ZIP archive (`main` branch release or snapshot).
- **Branch Tracking Mentioned in Docs:** `README.md` documents planned branching conventions:
  - `main` (Production)
  - `develop` (Integration)
  - Feature branches: `feature/person1-foundation`, `feature/person2-ai`, `feature/person3-frontend`, `feature/person4-policy-audit`.
- **Existing Ignore Rules:** `.gitignore` properly excludes `.env`, `node_modules/`, `venv/`, `__pycache__/`, `*.db`, and editor directories.

---

## 4. Architecture Overview

DATAEXPIRY implements a decoupled client-server architecture with an SQLite persistence layer:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND: React 18 + Vite                         │
│  - Dashboard.tsx             - AIInsights.tsx (Interactive)            │
│  - DataInventory.tsx         - PolicyManagement.tsx [PLACEHOLDER]      │
│  - RecordDetails.tsx         - AuditTrail.tsx [PLACEHOLDER]            │
│  - ExpiryManagement.tsx      - api.ts (Centralized Fetch Client)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST / JSON (Proxy :5173 -> :8000)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKEND: FastAPI + Pydantic                     │
│  - main.py (App entrypoint & CORS)                                     │
│  - core/security.py (Header-based Pseudo-RBAC)                         │
│  - api/routes.py (/api/health, /api/data, /api/ai/*)                   │
│  - api/policy_routes.py (/api/policies, /api/policies/evaluate)        │
│  - api/action_routes.py (/api/data/{id}/execute-action)                │
│  - api/audit_routes.py (/api/audit)                                    │
└───────────┬───────────────────────┬───────────────────────┬────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌───────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│    DATABASE LAYER     │ │    AI SERVICE     │ │   LIFECYCLE & AUDIT    │
│ SQLAlchemy 2.0 ORM    │ │ - Semantic NLP    │ │ - Policy Engine        │
│ SQLite / PostgreSQL   │ │ - Google Gemini   │ │ - Action Executor      │
│ Models:               │ │   REST Client     │ │ - Immutable Audit Log  │
│  • data_records       │ │ - Rule-based      │ │   Service              │
│  • retention_policies │ │   Fallback        │ │                        │
│  • audit_logs         │ │                   │ │                        │
└───────────────────────┘ └───────────────────┘ └────────────────────────┘
```

---

## 5. Main Application Entry Points

### 1. Backend Server Entrypoint
- **File:** `backend/app/main.py`
- **Command:** `uvicorn app.main:app --reload --port 8000`
- **Behavior:**
  - Invokes `Base.metadata.create_all(bind=engine)` at module load to generate SQLite tables if absent.
  - Configures CORS using `settings.get_cors_origins()`.
  - Mounts API routers with prefix `/api`:
    - `api_router` (`app/api/routes.py`)
    - `policy_router` (`app/api/policy_routes.py`)
    - `audit_router` (`app/api/audit_routes.py`)
    - `action_router` (`app/api/action_routes.py`)
  - Exposes root welcome endpoint `GET /`.

### 2. Frontend Application Entrypoint
- **Files:** `frontend/index.html` -> `frontend/src/main.tsx` -> `frontend/src/App.tsx`
- **Command:** `npm run dev` (starts Vite dev server on `http://localhost:5173`)
- **Behavior:**
  - Wraps routes inside `Layout.tsx` which includes the persistent sidebar `Navigation.tsx`.
  - Checks `/api/health` on mount to show backend connectivity badge.
  - Vite dev server proxies `/api` requests to `http://localhost:8000`.

### 3. Database Seeding Script
- **File:** `backend/seed_db.py`
- **Command:** `python seed_db.py` (run from `backend/`)
- **Behavior:**
  - Reads 20 synthetic records from `data/synthetic/records.json`.
  - Inserts non-duplicate records into `data_records`.
  - Inserts 3 demo policies (`POL-CUS-01`, `POL-TXN-01`, `POL-MKT-01`) into `retention_policies`.

---

## 6. Detailed Feature Inventory & Status Matrix

| Feature | Subsystem | File References | Status | Primary Defect / Blocker | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API Health & Welcome** | Backend & Frontend | `backend/app/api/routes.py`<br>`frontend/src/components/Layout.tsx` | **COMPLETE** | None. Returns 200 OK with service name and version. | Maintain. |
| **Data Record Catalog API** | Backend | `backend/app/api/routes.py`<br>`backend/app/services/data_service.py` | **COMPLETE** | None. Supports multi-field filtering (`category`, `status`, `sensitivity`) and pagination. | Maintain. |
| **Data Inventory UI** | Frontend | `frontend/src/pages/DataInventory.tsx` | **COMPLETE** | Create-record UI modal is missing. | Add record creation modal. |
| **Record Details Profile UI** | Frontend | `frontend/src/pages/RecordDetails.tsx` | **COMPLETE** | Missing action execution buttons (cannot trigger KEEP/REVIEW/ANONYMIZE/DELETE from page). | Add lifecycle action trigger buttons. |
| **Semantic Purpose Mismatch Engine** | Backend | `backend/app/services/ai_service.py` | **COMPLETE** | None. Comprehensive NLP clustering, domain matching, and Jaccard token analysis implemented. | Maintain. |
| **Google Gemini LLM Integration** | Backend | `backend/app/services/ai_service.py` | **COMPLETE** | Model ID in `.env.example` is `gemini-3.5-flash-lite` (check naming convention validity against Gemini API standard). | Verify model name compatibility. |
| **AI Batch Governance Audit** | Backend & Frontend | `backend/app/api/routes.py`<br>`frontend/src/pages/AIInsights.tsx` | **COMPLETE** | None. Scans database records, updates mismatch status, and refreshes UI. | Maintain. |
| **Purpose Mismatch Playground** | Backend & Frontend | `backend/app/api/routes.py`<br>`frontend/src/pages/PurposeMismatch.tsx` | **COMPLETE** | None. Interactive sandbox evaluates purpose-usage compatibility without DB mutation. | Maintain. |
| **Retention Policy Management API** | Backend | `backend/app/api/policy_routes.py`<br>`backend/app/services/policy_service.py` | **COMPLETE** | None. Full CRUD, duration parsing, category matching, and active filters. | Maintain. |
| **Retention Policy Evaluation Engine** | Backend | `backend/app/services/policy_service.py` | **COMPLETE** | None. Deterministic rules override AI: purpose mismatch strictly forces human REVIEW; active records kept. | Maintain. |
| **Policy Management UI** | Frontend | `frontend/src/pages/PolicyManagement.tsx` | **NOT IMPLEMENTED** | Static mockup with Target Feature banners. Does not list, create, edit, or evaluate policies. | Build functional React UI connected to `/api/policies`. |
| **Immutable Audit Logging API** | Backend | `backend/app/api/audit_routes.py`<br>`backend/app/services/audit_service.py` | **COMPLETE** | None. Atomic audit log creation, query filtering by record/action/user, pagination. | Maintain. |
| **Audit Trail UI** | Frontend | `frontend/src/pages/AuditTrail.tsx` | **NOT IMPLEMENTED** | Static mockup with Target Feature banners. Does not fetch or display audit logs. | Build functional React audit viewer connected to `/api/audit`. |
| **Lifecycle Action Execution** | Backend | `backend/app/api/action_routes.py`<br>`backend/app/services/lifecycle_service.py` | **PARTIAL** | Simulated deletion and anonymization only. Data is not erased or masked. | Implement real data masking/purging or document retention simulation boundary. |
| **Expiry Review Workflow** | Frontend | `frontend/src/pages/ExpiryManagement.tsx` | **PARTIAL** | Review queue is ephemeral React state in browser session; does not call backend action API. | Wire review actions to `/api/data/{id}/execute-action`. |
| **Role-Based Access Control (RBAC)** | Backend | `backend/app/core/security.py` | **BROKEN** | Insecure fallback: defaults to `ADMIN` when headers are missing. Anyone can impersonate any role. | Implement secure token-based authentication or strict dev guards. |
| **Database Migrations** | Backend | `backend/app/database/session.py` | **NOT IMPLEMENTED** | No Alembic migrations. Uses raw `Base.metadata.create_all`. | Add Alembic migration environment. |

---

## 7. End-to-End Workflow Analysis

### Workflow 1: Catalog Browsing & Search (WORKING)
1. **User Action:** User navigates to `/inventory`, types search keywords, or filters by category/status/sensitivity.
2. **Execution:** `DataInventory.tsx` executes `apiService.getDataRecords({ limit: 500 })`.
3. **Backend:** FastAPI routes to `GET /api/data`, `DataRecordService.get_records()` queries SQLite `data_records`.
4. **Data:** Reads `data_records` table, serializes to `List[DataRecordResponse]`.
5. **Output:** Table displays filtered list. Clicking record ID routes to `/records?id={record_id}`.

### Workflow 2: AI Purpose Mismatch Audit & Sandbox (WORKING)
1. **User Action:** User navigates to `/purpose-mismatch`, opens the sandbox playground, inputs purpose and usage, and clicks "Evaluate Compatibility".
2. **Execution:** `PurposeMismatch.tsx` executes `apiService.checkPurposeMismatch(request)`.
3. **Backend:** FastAPI routes to `POST /api/ai/check-mismatch`. Calls `AIService.analyze_record()`.
4. **Provider Path:**
   - If `GEMINI_API_KEY` configured: `GeminiAIProvider` queries Google Generative Language REST API.
   - If unconfigured or timed out (6s): Falls back automatically to rule-based semantic NLP engine (`evaluate_purpose_compatibility`).
5. **Output:** Returns `PurposeMismatchResult` with mismatch boolean, risk level, recommendation, and explanation.

### Workflow 3: Retention Policy Definition & Evaluation (DISCONNECTED AT UI)
1. **User Action:** User navigates to `/policy` expecting to view or create retention policies.
2. **UI Failure:** `PolicyManagement.tsx` displays static cards ("Target Feature 1: Rule Builder"). No network request is initiated.
3. **Backend State:** Full REST API exists at `GET /api/policies`, `POST /api/policies`, and `POST /api/policies/evaluate`. All tested and functional via pytest, but completely inaccessible from UI.

### Workflow 4: Lifecycle Action Execution (DISCONNECTED AT UI, SIMULATED AT BACKEND)
1. **User Action:** User inspects expired record on `/expiry` and clicks "Queue review".
2. **UI Failure:** Adds record ID to local React state array `queued: string[]`. No API call is made. Banner notes: *"Actions on this page only create a temporary review queue in this browser session."*
3. **Backend State:** `POST /api/data/{record_id}/execute-action` exists. When called:
   - Enforces RBAC permissions (`ADMIN` and `DATA_GOVERNANCE` can execute all; `PRIVACY_OFFICER` limited to `REVIEW` and `ANONYMIZE`).
   - If action is `DELETE`, sets `deletion_status = "Deleted"` and `status = "Expired"`. **Does not delete or erase record.**
   - If action is `ANONYMIZE`, sets `anonymization_status = "Anonymized"` and `status = "Archived"`. **Does not mask or hash data.**
   - Logs event to `audit_logs` atomically.

### Workflow 5: Compliance Audit Trail Verification (DISCONNECTED AT UI)
1. **User Action:** User navigates to `/audit` to inspect audit logs.
2. **UI Failure:** `AuditTrail.tsx` displays static cards ("Target Feature 1: Lifecycle Event Logs").
3. **Backend State:** Full REST API exists at `GET /api/audit` and `GET /api/audit/{record_id}`. Functional via pytest, but inaccessible from UI.

---

## 8. Build, Runtime, and Test Results

### Safe Inspection Checks Executed:

1. **Python Pip List Inspection:**
   - **Command:** `python -m pip list`
   - **Result:** PASSED (Conclusive)
   - **Output:** Python 3.13.2 installed. Global environment contains `fastapi` (0.142.2), `uvicorn` (0.54.0), `pydantic` (2.13.5), `pytest` (9.1.1), `httpx` (0.28.1).
   - **Missing Dependencies:** `sqlalchemy` and `pydantic-settings` are absent from the global environment.

2. **Backend Automated Test Suite Execution:**
   - **Command:** `pytest` (executed from `backend/`)
   - **Result:** FAILED DURING COLLECTION (Conclusive environment blocker)
   - **Error Output:**
     ```
     collected 0 items / 9 errors
     ERROR tests/test_ai_service.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_api.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_audit_service.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_db.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_lifecycle_actions.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_person4_api_integration.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_phase1_models_schemas.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_policy_engine.py - ModuleNotFoundError: No module named 'sqlalchemy'
     ERROR tests/test_rbac_security.py - ModuleNotFoundError: No module named 'sqlalchemy'
     Interrupted: 9 errors during collection
     ```
   - **Root Cause:** Virtual environment has not been created; global Python lacks `sqlalchemy`. Per audit rules, no packages were installed.

3. **Frontend Typecheck & Lint Execution:**
   - **Command:** `npm run lint` (which runs `tsc --noEmit`) from `frontend/`
   - **Result:** FAILED (Conclusive environment blocker)
   - **Error Output:**
     ```
     > tsc --noEmit
     'tsc' is not recognized as an internal or external command, operable program or batch file.
     ```
   - **Root Cause:** `frontend/node_modules/` does not exist (`npm install` has not been run). Per audit rules, dependencies were not installed.

---

## 9. Confirmed Defects and Suspected Risks

### Confirmed Defects (Backed by Code Evidence)

1. **[OBSERVED FAILURE] Missing Frontend UI for Policy Management:**
   - **Evidence:** `frontend/src/pages/PolicyManagement.tsx` (lines 14–43) contains hardcoded placeholder HTML.
   - **Impact:** Administrators cannot configure or inspect retention policies from the UI.

2. **[OBSERVED FAILURE] Missing Frontend UI for Compliance Audit Trail:**
   - **Evidence:** `frontend/src/pages/AuditTrail.tsx` (lines 14–43) contains hardcoded placeholder HTML.
   - **Impact:** Compliance auditors cannot inspect audit event records or verify deletion proofs from the UI.

3. **[OBSERVED FAILURE] Missing API Client Integration for Policies, Audit, and Actions:**
   - **Evidence:** `frontend/src/services/api.ts` (lines 1–150) defines methods for health, data records, and AI governance, but zero methods for `/api/policies`, `/api/audit`, or `/api/data/{id}/execute-action`.
   - **Impact:** Frontend code has no abstraction to communicate with Person 4's backend modules.

4. **[OBSERVED FAILURE] Ephemeral Review Queue in Expiry Management:**
   - **Evidence:** `frontend/src/pages/ExpiryManagement.tsx` (lines 15, 20) only pushes record IDs to a local React state array `queued`.
   - **Impact:** Review decisions are lost upon page reload and never recorded in the database or audit log.

5. **[OBSERVED FAILURE] Insecure Header-Based RBAC Defaulting to ADMIN:**
   - **Evidence:** `backend/app/core/security.py` (lines 23–38):
     ```python
     if x_user_role and x_user_role.strip():
         ...
     else:
         role = UserRole.ADMIN
     ```
   - **Impact:** Omitting `X-User-Role` grants complete administrator privileges.

### Suspected Risks & Architectural Weaknesses

1. **[REASONED RISK] Simulated Deletion Compliance Hazard:**
   - **Evidence:** `backend/app/services/lifecycle_service.py` (lines 91–99). The `DELETE` action explicitly comments: *"simulated deletion only; data preserved for compliance"*.
   - **Risk:** Under GDPR Article 17 ("Right to Erasure"), organizations must permanently erase personal data. Storing personal records in plaintext after claiming "Deleted" status introduces legal liability unless clearly partitioned into a tombstone or archival store.

2. **[REASONED RISK] Gemini Model String Naming:**
   - **Evidence:** `backend/app/core/config.py` (line 26) specifies `GEMINI_MODEL: str = "gemini-3.5-flash-lite"`.
   - **Risk:** Standard Google Gemini API models are currently named `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`, etc. If `gemini-3.5-flash-lite` is an invalid model identifier on the endpoint, Gemini requests will return HTTP 404/400 and immediately fall back to rule-based evaluation.

3. **[REASONED RISK] Lack of Database Migration Engine:**
   - **Evidence:** No `alembic.ini` or migration scripts exist in `backend/`. Table creation relies on `Base.metadata.create_all`.
   - **Risk:** Future schema updates will not be applied to existing SQLite or PostgreSQL databases automatically.

---

## 10. Prioritized Completion Roadmap

```
[P0: Critical]  Environment Setup (Venv + NPM) & RBAC Security Hardening
      │
      ▼
[P1: Core]      Frontend API Service Extension (Policies, Audit, Actions)
      │
      ▼
[P1: Core]      Implement PolicyManagement.tsx & AuditTrail.tsx Views
      │
      ▼
[P1: Core]      Wire Action Execution to ExpiryManagement & RecordDetails
      │
      ▼
[P2: Reliab]    Implement Real Data Masking (Anonymize) & Purge (Delete)
      │
      ▼
[P3: Polish]    Alembic Migrations, Audit CSV Export, Dockerfile for LinuxONE
```

### Milestone Breakdown:
- **P0 — Critical:**
  - `TASK-P0-01`: Create Python virtual environment and install backend dependencies.
  - `TASK-P0-02`: Run `npm install` in frontend.
  - `TASK-P0-03`: Secure `get_current_user` in `security.py` so unauthenticated requests do not default to `ADMIN`.
- **P1 — Core Functionality:**
  - `TASK-P1-01`: Add Policy, Audit, and Action methods & TypeScript interfaces to `frontend/src/services/api.ts` and `frontend/src/types/index.ts`.
  - `TASK-P1-02`: Build complete `PolicyManagement.tsx` view (Policy table, Create Policy modal, Run Evaluation button).
  - `TASK-P1-03`: Build complete `AuditTrail.tsx` view (Filterable audit table, record audit drawer, timeline view).
  - `TASK-P1-04`: Connect "Queue review" and lifecycle action buttons in `ExpiryManagement.tsx` and `RecordDetails.tsx` to `apiService.executeAction()`.
- **P2 — Reliability:**
  - `TASK-P2-01`: Implement data masking for `ANONYMIZE` (e.g., redact names/emails/identifiers).
  - `TASK-P2-02`: Initialize Alembic database migrations.
- **P3 — Polish & Deployment:**
  - `TASK-P3-01`: Export audit logs to CSV/JSON format.
  - `TASK-P3-02`: Create containerized Dockerfile and docker-compose configuration.

---

## 11. Open Questions & Missing Information

1. **Gemini API Model Compatibility:** Does the team have access to a custom Google preview model named `gemini-3.5-flash-lite`, or should standard production model strings like `gemini-1.5-flash` or `gemini-2.0-flash` be used?
2. **Deletion Semantics:** Is DATAEXPIRY intended strictly as a **governance metadata catalog** (where data resides in upstream external source databases and local records are only markers), or is it expected to perform real row deletion or cryptographic zeroing?
3. **Authentication Strategy:** What identity provider will be used in production (e.g. OAuth2/OIDC, LDAP, Keycloak, or JWT tokens)? Should the frontend provide a user/role switcher for demonstration purposes?
