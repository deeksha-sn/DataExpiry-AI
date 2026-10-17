# DATAEXPIRY — Audit Evidence & Verification Log

**Audit Execution Date:** October 16, 2026  
**Auditor:** Technical Auditor & Staff QA Architect  
**Workspace:** `C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main`  
**Execution Context:** Non-destructive, read-only diagnostic inspection  

---

## 1. Environment & Workspace Diagnostics

### Command 1.1: Git Repository Status Verification
- **Statement Type:** [VERIFIED FACT]
- **Exact Command Executed:**
  ```powershell
  git status; git branch -a; git remote -v; git log -n 5 --oneline
  ```
- **Execution Working Directory:** `C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main`
- **Output:**
  ```
  fatal: not a git repository (or any of the parent directories): .git
  fatal: not a git repository (or any of the parent directories): .git
  fatal: not a git repository (or any of the parent directories): .git
  fatal: not a git repository (or any of the parent directories): .git
  ```
- **Conclusive Evidence:** The workspace is not an active git repository. The folder name `DataExpiry-AI-main` confirms this is an extracted archive from GitHub's ZIP download format (`main` branch snapshot).

---

### Command 1.2: Host Runtime Environment Verification
- **Statement Type:** [VERIFIED FACT]
- **Exact Command Executed:**
  ```powershell
  python --version; node --version; npm --version
  ```
- **Output:**
  ```
  Python 3.13.2
  v24.15.0
  11.12.1
  ```
- **Conclusive Evidence:** The host machine possesses modern runtimes (Python 3.13.2, Node.js v24.15.0, npm 11.12.1), fulfilling all stated prerequisites.

---

### Command 1.3: Installed Python Package Inspection
- **Statement Type:** [VERIFIED FACT]
- **Exact Command Executed:**
  ```powershell
  python -m pip list
  ```
- **Key Output Findings:**
  - `fastapi` version: `0.142.2`
  - `pydantic` version: `2.13.5`
  - `pydantic_core` version: `2.46.5`
  - `pytest` version: `9.1.1`
  - `uvicorn` version: `0.54.0`
  - `httpx` version: `0.28.1`
  - `starlette` version: `1.7.0`
  - **Absent packages:** `sqlalchemy` and `pydantic-settings` are NOT present in the global python environment.

---

### Command 1.4: Direct SQLAlchemy Import Test
- **Statement Type:** [VERIFIED FACT]
- **Exact Command Executed:**
  ```powershell
  python -c "import sqlalchemy; import pydantic_settings; print('SQLAlchemy:', sqlalchemy.__version__); print('pydantic-settings OK')"
  ```
- **Exit Code:** 1
- **Output:**
  ```
  Traceback (most recent call last):
    File "<string>", line 1, in <module>
      import sqlalchemy; import pydantic_settings; print('SQLAlchemy:', sqlalchemy.__version__); print('pydantic-settings OK')
      ^^^^^^^^^^^^^^^^^
  ModuleNotFoundError: No module named 'sqlalchemy'
  ```
- **Conclusive Evidence:** Any backend script requiring SQLAlchemy cannot execute in the uninitialized global environment without a virtual environment.

---

### Command 1.5: Dependency Directory Existence Check
- **Statement Type:** [VERIFIED FACT]
- **Exact Command Executed:**
  ```powershell
  Test-Path frontend\node_modules; Test-Path backend\venv; Test-Path backend\.venv; Test-Path venv; Test-Path .venv
  ```
- **Output:**
  ```
  False
  False
  False
  False
  False
  ```
- **Conclusive Evidence:** No Python virtual environment has been created, and frontend `node_modules/` has not been installed.

---

## 2. Test Execution & Build Health Diagnostics

### Command 2.1: Backend Pytest Suite Run
- **Statement Type:** [OBSERVED FAILURE]
- **Exact Command Executed:**
  ```powershell
  pytest
  ```
- **Execution Working Directory:** `C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main\backend`
- **Exit Code:** 1
- **Output:**
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
  rootdir: C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main\backend
  plugins: platformdirs-4.13.0, anyio-4.15.1
  collected 0 items / 9 errors

  =================================== ERRORS ====================================
  __________________ ERROR collecting tests/test_ai_service.py __________________
  tests\test_ai_service.py:13: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  _____________________ ERROR collecting tests/test_api.py ______________________
  tests\test_api.py:3: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ________________ ERROR collecting tests/test_audit_service.py _________________
  tests\test_audit_service.py:2: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ______________________ ERROR collecting tests/test_db.py ______________________
  tests\test_db.py:2: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ______________ ERROR collecting tests/test_lifecycle_actions.py _______________
  tests\test_lifecycle_actions.py:2: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ___________ ERROR collecting tests/test_person4_api_integration.py ____________
  tests\test_person4_api_integration.py:3: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ____________ ERROR collecting tests/test_phase1_models_schemas.py _____________
  tests\test_phase1_models_schemas.py:3: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ________________ ERROR collecting tests/test_policy_engine.py _________________
  tests\test_policy_engine.py:3: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  ________________ ERROR collecting tests/test_rbac_security.py _________________
  tests\test_rbac_security.py:3: in <module>
      from sqlalchemy import create_engine
  E   ModuleNotFoundError: No module named 'sqlalchemy'
  =========================== short test summary info ===========================
  ERROR tests/test_ai_service.py
  ERROR tests/test_api.py
  ERROR tests/test_audit_service.py
  ERROR tests/test_db.py
  ERROR tests/test_lifecycle_actions.py
  ERROR tests/test_person4_api_integration.py
  ERROR tests/test_phase1_models_schemas.py
  ERROR tests/test_policy_engine.py
  ERROR tests/test_rbac_security.py
  !!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!
  ======================== 1 warning, 9 errors in 1.17s =========================
  ```
- **Conclusive Evidence:** All 9 backend test files exist and are syntactically valid pytest suites, but failed during test discovery/collection because `sqlalchemy` is missing in the host environment. Per audit rules, no installation commands were run.

---

### Command 2.2: Frontend TypeScript & Lint Check
- **Statement Type:** [OBSERVED FAILURE]
- **Exact Command Executed:**
  ```powershell
  npm run lint
  ```
- **Execution Working Directory:** `C:\Users\nathi\Desktop\IBM\DataExpiry-AI-main\frontend`
- **Exit Code:** 1
- **Output:**
  ```
  > dataexpiry-frontend@1.0.0 lint
  > tsc --noEmit

  'tsc' is not recognized as an internal or external command,
  operable program or batch file.
  ```
- **Conclusive Evidence:** The TypeScript compiler (`tsc`) cannot execute because `frontend/node_modules/` has not been installed via `npm install`.

---

## 3. Code Inspection & Architectural Evidence

### Evidence 3.1: Security Vulnerability in RBAC Fallback
- **Statement Type:** [VERIFIED FACT]
- **File Reference:** `backend/app/core/security.py` (lines 23–38)
- **Code Snippet:**
  ```python
  def get_current_user(
      x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
      x_user_role: Optional[str] = Header(None, alias="X-User-Role")
  ) -> CurrentUser:
      user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else "local_dev_user"

      if x_user_role and x_user_role.strip():
          role_str = x_user_role.strip().upper()
          try:
              role = UserRole(role_str)
          except ValueError:
              raise HTTPException(status_code=403, detail=...)
      else:
          role = UserRole.ADMIN
      return CurrentUser(user_id=user_id, role=role)
  ```
- **Audit Conclusion:** Any request made without the `X-User-Role` header is automatically elevated to `ADMIN` permissions, bypassing all access restrictions.

---

### Evidence 3.2: Simulated Deletion and Anonymization Logic
- **Statement Type:** [VERIFIED FACT]
- **File Reference:** `backend/app/services/lifecycle_service.py` (lines 90–106)
- **Code Snippet:**
  ```python
  if action_upper == "DELETE":
      # SIMULATED DELETION ONLY:
      # - No SQL DELETE
      # - No row removal
      # - No wiping/clearing of sensitive data columns
      record.deletion_status = "Deleted"
      if record.status != "Expired":
          record.status = "Expired"
      new_status = record.status
      message = f"Record '{record.record_id}' marked as Deleted (simulated deletion; data preserved for compliance)."

  elif action_upper == "ANONYMIZE":
      record.anonymization_status = "Anonymized"
      record.status = "Archived"
      new_status = "Archived"
      message = f"Record '{record.record_id}' marked as Anonymized and Archived."
  ```
- **Audit Conclusion:** The backend does not actually erase rows or mask sensitive personal data upon `DELETE` or `ANONYMIZE` actions.

---

### Evidence 3.3: Placeholder Content in Frontend Pages
- **Statement Type:** [OBSERVED FAILURE]
- **Command Executed:**
  ```powershell
  Select-String -Path "frontend\src\**\*.tsx" -Pattern "Target Feature"
  ```
- **Output:**
  ```
  frontend\src\pages\AuditTrail.tsx:26:            <span className="text-xs font-mono text-slate-400">Target Feature 1</span>
  frontend\src\pages\AuditTrail.tsx:32:            <span className="text-xs font-mono text-slate-400">Target Feature 2</span>
  frontend\src\pages\AuditTrail.tsx:38:            <span className="text-xs font-mono text-slate-400">Target Feature 3</span>
  frontend\src\pages\PolicyManagement.tsx:26:            <span className="text-xs font-mono text-slate-400">Target Feature 1</span>
  frontend\src\pages\PolicyManagement.tsx:32:            <span className="text-xs font-mono text-slate-400">Target Feature 2</span>
  frontend\src\pages\PolicyManagement.tsx:38:            <span className="text-xs font-mono text-slate-400">Target Feature 3</span>
  ```
- **Audit Conclusion:** Both `PolicyManagement.tsx` and `AuditTrail.tsx` contain literal "Target Feature" mockup placeholder banners and initiate zero backend network requests.

---

### Evidence 3.4: Ephemeral Review Queue in Expiry Management
- **Statement Type:** [OBSERVED FAILURE]
- **File Reference:** `frontend/src/pages/ExpiryManagement.tsx` (lines 15, 19, 20)
- **Code Snippet:**
  ```tsx
  const [queued, setQueued] = useState<string[]>([]);
  ...
  <div className="rounded-lg border border-sky-900/70 bg-sky-950/30 p-4 text-sm text-sky-200">
    Actions on this page only create a temporary review queue in this browser session. No records are deleted, altered, or sent to a workflow API.
  </div>
  ...
  <button onClick={()=>setQueued(q=>q.includes(r.record_id)?q:[...q,r.record_id])}>
    {queued.includes(r.record_id)?'Queued for review':'Queue review'}
  </button>
  ```
- **Audit Conclusion:** The review queue does not persist review requests to the database and fails to trigger `/api/data/{record_id}/execute-action`.

---

### Evidence 3.5: Missing Endpoints in Frontend API Service
- **Statement Type:** [VERIFIED FACT]
- **File Reference:** `frontend/src/services/api.ts` (lines 1–150)
- **Inspection Summary:**
  - Contains: `getHealth()`, `getDataRecords()`, `getDataRecord()`, `createDataRecord()`, `runBatchAiAnalysis()`, `analyzeRecord()`, `checkPurposeMismatch()`, `getAIGovernanceSummary()`.
  - Missing: Zero methods for `policies`, `audit`, or `execute-action`.

---

## 4. Reasoned Risks & Recommendations

1. **[REASONED RISK] Gemini Model String:**
   - In `backend/app/core/config.py` (line 26), `GEMINI_MODEL: str = "gemini-3.5-flash-lite"`.
   - Reasoned Risk: Google Generative Language API uses identifiers like `gemini-1.5-flash` or `gemini-2.0-flash`. Calling an unreleased/invalid identifier results in HTTP 404, which immediately activates the rule-based fallback.
   - Recommendation: Verify model availability with an API key, or default to `gemini-1.5-flash`.

2. **[REASONED RISK] GDPR Article 17 Non-Compliance in Production:**
   - The current `DELETE` behavior only updates metadata flags without row destruction.
   - Recommendation: For enterprise deployment, provide an option for true cryptographic erasure or purge from `data_records` table while preserving the immutable audit log entry.
