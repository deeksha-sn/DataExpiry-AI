# DATAEXPIRY — Engineering Issues & Prioritized Completion Roadmap

**Document Version:** 1.0.0  
**Target Execution:** Engineering pair-programming sprint (ChatGPT + Human Lead)  

---

## 1. Backlog Overview & Priority Framework

- **P0 — Critical:** Security bypasses, uninitialized environment blockers, test collection failures. Must be addressed first before modifying application behavior.
- **P1 — Core Functionality:** Frontend UI implementations for Policy Management, Audit Trail, and Lifecycle Action triggers required to close the loop on Person 3 & Person 4 responsibilities.
- **P2 — Reliability & Compliance:** Real data masking / deletion implementation, database migration framework, and error boundary handling.
- **P3 — Polish & Deployment:** Audit report exports, Docker containerization for LinuxONE, and CI/CD automation.

---

## 2. Priority 0: Critical (Blockers & Security)

### TASK-P0-01: Establish Backend Virtual Environment & Install Dependencies
- **Severity:** P0 — Critical Blocker
- **Reason:** Running `pytest` currently fails during test collection with 9 errors (`ModuleNotFoundError: No module named 'sqlalchemy'`) because no virtual environment exists and global Python lacks required dependencies.
- **Relevant Files:** `backend/requirements.txt`, `backend/app/database/session.py`
- **Dependencies:** None
- **Estimated Effort:** XS (10–15 minutes)
- **Acceptance Criteria:**
  1. A Python virtual environment (`backend/venv`) is created and active.
  2. All packages from `backend/requirements.txt` (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `python-dotenv`, `pytest`, `httpx`) are installed cleanly without version conflicts.
  3. `python -c "import sqlalchemy, pydantic_settings; print('OK')"` exits with code 0.
- **Verification Command:**
  ```bash
  cd backend
  python -m venv venv
  # On Windows:
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  pytest
  ```

---

### TASK-P0-02: Install Frontend Dependencies & Verify Typecheck
- **Severity:** P0 — Critical Blocker
- **Reason:** Running `npm run lint` or `npm run build` currently fails because `frontend/node_modules/` is missing (`'tsc' is not recognized`).
- **Relevant Files:** `frontend/package.json`, `frontend/package-lock.json`
- **Dependencies:** None
- **Estimated Effort:** XS (5–10 minutes)
- **Acceptance Criteria:**
  1. `frontend/node_modules` exists with all packages installed per `package-lock.json`.
  2. Running `npm run lint` executes `tsc --noEmit` and reports any static typing errors.
  3. Running `npm run build` produces a production bundle in `frontend/dist/`.
- **Verification Command:**
  ```bash
  cd frontend
  npm install
  npm run lint
  npm run build
  ```

---

### TASK-P0-03: Eliminate Insecure RBAC Default ADMIN Bypass
- **Severity:** P0 — Critical Security Vulnerability
- **Reason:** In `backend/app/core/security.py`, `get_current_user` defaults unauthenticated requests to `UserRole.ADMIN` and `user_id = "local_dev_user"`. Any user or external caller can bypass all authorization controls simply by omitting headers or supplying `X-User-Role: ADMIN`.
- **Relevant Files:** `backend/app/core/security.py`, `backend/tests/test_rbac_security.py`
- **Dependencies:** TASK-P0-01
- **Estimated Effort:** S (1–2 hours)
- **Acceptance Criteria:**
  1. When running in standard mode (`ENVIRONMENT != "development"`), requests lacking a valid authentication credential or role header are rejected with HTTP 401 Unauthorized or HTTP 403 Forbidden.
  2. If a local dev bypass is maintained, it must be explicitly guarded behind a strict configuration flag (e.g. `ALLOW_DEV_HEADER_AUTH=True`), default to `VIEWER` rather than `ADMIN`, and log a security warning on every invocation.
  3. All RBAC tests in `test_rbac_security.py` pass with updated security assertions.
- **Verification Command:**
  ```bash
  pytest backend/tests/test_rbac_security.py
  ```

---

## 3. Priority 1: Core Functionality (Closing Feature Gaps)

### TASK-P1-01: Extend Frontend API Service & TypeScript Interfaces
- **Severity:** P1 — Core Functional Blocker
- **Reason:** `frontend/src/services/api.ts` contains no methods for policy management, audit logging, or action execution. `frontend/src/types/index.ts` lacks interfaces for `PolicyRule`, `PolicyEvaluation`, and `AuditLog`.
- **Relevant Files:** `frontend/src/types/index.ts`, `frontend/src/services/api.ts`
- **Dependencies:** TASK-P0-02
- **Estimated Effort:** S (2–3 hours)
- **Acceptance Criteria:**
  1. `frontend/src/types/index.ts` exports:
     - `PolicyRule`, `PolicyRuleCreateInput`, `PolicyRuleUpdateInput`
     - `PolicyEvaluationItem`, `PolicyEvaluationSummary`
     - `AuditLogEntry`, `AuditFilterParams`
     - `LifecycleActionRequest`, `LifecycleActionResponse`
  2. `frontend/src/services/api.ts` provides methods:
     - `getPolicies(activeOnly?: boolean)` -> `Promise<PolicyRule[]>`
     - `createPolicy(data: PolicyRuleCreateInput)` -> `Promise<PolicyRule>`
     - `updatePolicy(id: number, data: PolicyRuleUpdateInput)` -> `Promise<PolicyRule>`
     - `deactivatePolicy(id: number)` -> `Promise<PolicyRule>`
     - `evaluatePolicies(params?: { asOfDate?: string; expiringSoonDays?: number; category?: string })` -> `Promise<PolicyEvaluationSummary>`
     - `getAuditLogs(params?: AuditFilterParams)` -> `Promise<AuditLogEntry[]>`
     - `getRecordAuditLogs(recordId: string)` -> `Promise<AuditLogEntry[]>`
     - `executeLifecycleAction(recordId: string, action: string, reason?: string)` -> `Promise<LifecycleActionResponse>`
  3. `apiService` attaches configurable or current role headers (`X-User-Role`, `X-User-Id`) to satisfy backend RBAC requirements.
- **Verification Command:**
  ```bash
  cd frontend
  npm run lint
  ```

---

### TASK-P1-02: Implement Interactive Policy Management UI
- **Severity:** P1 — Core Functionality
- **Reason:** `frontend/src/pages/PolicyManagement.tsx` is currently a static placeholder displaying target feature banners with no live data.
- **Relevant Files:** `frontend/src/pages/PolicyManagement.tsx`
- **Dependencies:** TASK-P1-01
- **Estimated Effort:** M (4–6 hours)
- **Acceptance Criteria:**
  1. Displays a table of all existing retention policies fetched from `GET /api/policies` with rule code, category, retention period/days, action on expiry, and active status toggle.
  2. Includes a "Create New Policy" modal dialog with validation for rule code, category, duration string (e.g. `2 years`), and action selection (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`).
  3. Allows soft deactivation / activation toggle for policies.
  4. Includes a "Run Policy Evaluation" button that calls `POST /api/policies/evaluate` and displays summary cards (Active, Expiring Soon, Expired, and recommended actions) along with evaluated records.
- **Verification Command:** Manual UI verification on `http://localhost:5173/policy`. Verify network tab shows successful `GET /api/policies` and `POST /api/policies/evaluate`.

---

### TASK-P1-03: Implement Compliance Audit Trail UI
- **Severity:** P1 — Core Functionality
- **Reason:** `frontend/src/pages/AuditTrail.tsx` is currently a static placeholder with target feature banners.
- **Relevant Files:** `frontend/src/pages/AuditTrail.tsx`
- **Dependencies:** TASK-P1-01
- **Estimated Effort:** M (4–5 hours)
- **Acceptance Criteria:**
  1. Displays an immutable audit event table fetched from `GET /api/audit` showing timestamp, affected record ID, action executed (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`), actor user/role, previous status, new status, and compliance reason.
  2. Includes filter controls for Action, User, and Record ID search.
  3. Includes an expandable row or drawer to inspect full event details, including governing policy rule and AI recommendation state at event time.
- **Verification Command:** Manual UI verification on `http://localhost:5173/audit`. Verify network tab shows successful `GET /api/audit`.

---

### TASK-P1-04: Wire Action Execution to Expiry Management & Record Details
- **Severity:** P1 — Core Functionality
- **Reason:** In `ExpiryManagement.tsx`, clicking "Queue review" only updates an ephemeral React state array that is discarded on refresh. In `RecordDetails.tsx`, no action buttons exist.
- **Relevant Files:** `frontend/src/pages/ExpiryManagement.tsx`, `frontend/src/pages/RecordDetails.tsx`
- **Dependencies:** TASK-P1-01
- **Estimated Effort:** S (2–3 hours)
- **Acceptance Criteria:**
  1. In `ExpiryManagement.tsx`, clicking "Queue review" calls `apiService.executeLifecycleAction(record.record_id, 'REVIEW', reason)` and updates the record status to "In Review".
  2. In `RecordDetails.tsx`, an "Execute Lifecycle Action" button group allows authorized roles to trigger `KEEP`, `REVIEW`, `ANONYMIZE`, or `DELETE` with an optional confirmation modal and reason input.
  3. Action execution creates a visible audit entry in `AuditTrail.tsx`.
- **Verification Command:** Execute an action in `RecordDetails.tsx` and verify that `GET /api/audit` reflects the new event with matching timestamp and actor.

---

## 4. Priority 2: Reliability & Compliance Integrity

### TASK-P2-01: Implement Real Data Masking & Purging for Lifecycle Actions
- **Severity:** P2 — Compliance & Data Integrity
- **Reason:** In `LifecycleService.execute_action`, `DELETE` and `ANONYMIZE` actions are currently simulated: records remain in SQLite and continue to be served by `/api/data`. Under GDPR Article 17, true erasure or strict tombstoning is required.
- **Relevant Files:** `backend/app/services/lifecycle_service.py`, `backend/app/services/data_service.py`, `backend/tests/test_lifecycle_actions.py`
- **Dependencies:** TASK-P0-01
- **Estimated Effort:** M (3–4 hours)
- **Acceptance Criteria:**
  1. For `ANONYMIZE`: Sensitive fields (e.g. `owner`, specific identifier strings) are masked or pseudonymized using SHA-256 hashes or `[REDACTED]` markers while preserving non-PII operational category metadata.
  2. For `DELETE`: Provide a configurable setting:
     - Soft deletion with catalog filtering: `status = "Deleted"`, excluded from standard `GET /api/data` queries unless `include_deleted=true` is explicitly requested by `ADMIN`.
     - Permanent purge: physical removal from `data_records` table while preserving the corresponding immutable `audit_logs` record.
  3. Update unit tests in `test_lifecycle_actions.py` to assert that masked/deleted data conforms to privacy expectations.
- **Verification Command:**
  ```bash
  pytest backend/tests/test_lifecycle_actions.py
  ```

---

### TASK-P2-02: Set Up Alembic Database Migration Framework
- **Severity:** P2 — Database Maintainability
- **Reason:** The application relies on `Base.metadata.create_all`, which cannot alter existing tables or add columns without deleting the database file.
- **Relevant Files:** `backend/alembic.ini`, `backend/alembic/`, `backend/app/database/session.py`
- **Dependencies:** TASK-P0-01
- **Estimated Effort:** S (2 hours)
- **Acceptance Criteria:**
  1. `alembic init` configured with `target_metadata = Base.metadata`.
  2. Initial migration script generated covering `data_records`, `retention_policies`, and `audit_logs`.
  3. `alembic upgrade head` runs cleanly on fresh SQLite and PostgreSQL test databases.
- **Verification Command:**
  ```bash
  cd backend
  alembic upgrade head
  ```

---

## 5. Priority 3: Polish & Deployment

### TASK-P3-01: Audit Log Export to CSV & JSON
- **Severity:** P3 — Auditor Experience
- **Reason:** Compliance auditors need downloadable evidence of retention enforcement and deletion proofs for external compliance audits.
- **Relevant Files:** `frontend/src/pages/AuditTrail.tsx`, `backend/app/api/audit_routes.py`
- **Dependencies:** TASK-P1-03
- **Estimated Effort:** S (2 hours)
- **Acceptance Criteria:**
  1. "Export CSV" and "Export JSON" buttons on `AuditTrail.tsx` generate downloadable client-side files of filtered audit records.
- **Verification Command:** Click "Export CSV" and inspect the downloaded file for correct columns.

---

### TASK-P3-02: Containerization & LinuxONE Deployment Blueprint
- **Severity:** P3 — Deployment Readiness
- **Reason:** Mentioned in project roadmap as a primary deployment target for enterprise scalability.
- **Relevant Files:** `Dockerfile`, `docker-compose.yml`, `docs/ARCHITECTURE.md`
- **Dependencies:** TASK-P0-01, TASK-P0-02
- **Estimated Effort:** M (3–4 hours)
- **Acceptance Criteria:**
  1. Multi-stage `Dockerfile` building frontend assets and serving FastAPI via Uvicorn.
  2. `docker-compose.yml` orchestrating FastAPI backend, PostgreSQL database, and optional Redis cache.
  3. Container builds and runs on Linux s390x / x86_64 architectures.
- **Verification Command:**
  ```bash
  docker compose build
  docker compose up -d
  curl http://localhost:8000/api/health
  ```
