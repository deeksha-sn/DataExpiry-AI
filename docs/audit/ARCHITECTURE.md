# DATAEXPIRY — Technical Architecture & Component Blueprint

**Document Version:** 1.0.0  
**Target Audience:** Staff Engineers, ChatGPT pair-programming agents, Frontend/Backend developers  
**Status:** Audit Reconstructed Architecture

---

## 1. High-Level System Architecture

DATAEXPIRY is structured as a modern decoupled client-server architecture consisting of three primary layers:
1. **Frontend Presentation Layer:** Single-Page Application (SPA) built with React 18, TypeScript, Tailwind CSS, and Vite.
2. **Backend Application Layer:** High-performance asynchronous API built with FastAPI, Pydantic v2, and SQLAlchemy 2.0.
3. **Storage & Engine Layer:** Relational persistence (SQLite default, PostgreSQL ready), an NLP semantic analysis engine, and deterministic policy rule governance.

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 18 + Vite :5173)"]
        UI_Dash["Dashboard\n(Dashboard.tsx)"]
        UI_Inv["Data Inventory\n(DataInventory.tsx)"]
        UI_Rec["Record Details\n(RecordDetails.tsx)"]
        UI_Exp["Expiry Queue\n(ExpiryManagement.tsx)"]
        UI_AI["AI Insights & Purpose\n(PurposeMismatch.tsx / AIInsights.tsx)"]
        UI_Pol["Policy Management\n(PolicyManagement.tsx) [MOCKUP]"]
        UI_Aud["Audit Trail\n(AuditTrail.tsx) [MOCKUP]"]
        API_SVC["apiService (api.ts)\nCentralized Fetch API"]
    end

    subgraph Server["Backend Application (FastAPI :8000)"]
        CORS["CORS Middleware"]
        SEC["Security & RBAC\n(core/security.py)"]
        
        subgraph Endpoints["API Route Handlers (/api)"]
            EP_Data["Data & Catalog Routes\n(api/routes.py)"]
            EP_AI["AI & Governance Routes\n(api/routes.py)"]
            EP_Pol["Policy Routes\n(api/policy_routes.py)"]
            EP_Act["Lifecycle Action Routes\n(api/action_routes.py)"]
            EP_Aud["Audit Routes\n(api/audit_routes.py)"]
        end

        subgraph Services["Core Business Logic Services"]
            SVC_Data["DataRecordService\n(data_service.py)"]
            SVC_AI["AIService & GeminiAIProvider\n(ai_service.py)"]
            SVC_Pol["PolicyService\n(policy_service.py)"]
            SVC_Life["LifecycleService\n(lifecycle_service.py)"]
            SVC_Aud["AuditService\n(audit_service.py)"]
        end
    end

    subgraph External["External Integrations"]
        GEMINI["Google Gemini REST API\n(v1beta models)"]
    end

    subgraph Storage["Persistence Layer (SQLAlchemy 2.0)"]
        DB_Records[("data_records\n(DataRecordModel)")]
        DB_Policies[("retention_policies\n(PolicyRuleModel)")]
        DB_Audit[("audit_logs\n(AuditLogModel)")]
    end

    %% Client communication
    UI_Dash --> API_SVC
    UI_Inv --> API_SVC
    UI_Rec --> API_SVC
    UI_Exp --> API_SVC
    UI_AI --> API_SVC
    UI_Pol -.->|Needs Connection| API_SVC
    UI_Aud -.->|Needs Connection| API_SVC
    
    API_SVC -->|HTTP REST JSON| CORS
    CORS --> SEC
    SEC --> Endpoints

    %% Route to Service dispatch
    EP_Data --> SVC_Data
    EP_AI --> SVC_AI
    EP_Pol --> SVC_Pol
    EP_Act --> SVC_Life
    EP_Aud --> SVC_Aud

    %% Service interactions
    SVC_Life --> SVC_Aud
    SVC_Life --> SVC_Data
    SVC_Pol --> SVC_Data
    SVC_AI --> SVC_Data
    SVC_AI -->|HTTPS REST| GEMINI

    %% Service to DB
    SVC_Data --> DB_Records
    SVC_Pol --> DB_Policies
    SVC_Aud --> DB_Audit
    SVC_Life --> DB_Records
    SVC_Life --> DB_Audit
```

---

## 2. Component Directory & File Responsibility Map

```
DataExpiry-AI-main/
│
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI Application Entrypoint, CORS, and Router mounting
│   │   ├── api/
│   │   │   ├── routes.py             # Health check, Data Record CRUD, AI Batch & Sandbox endpoints
│   │   │   ├── policy_routes.py      # Retention Policy CRUD and Policy Evaluation endpoints
│   │   │   ├── action_routes.py      # Lifecycle Action execution (KEEP, REVIEW, ANONYMIZE, DELETE)
│   │   │   ├── audit_routes.py       # Immutable audit log query endpoints
│   │   │   └── __init__.py           # Route exports
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic BaseSettings (env loading, CORS, Gemini keys)
│   │   │   └── security.py           # Header-based RBAC dependencies (UserRole, require_role)
│   │   ├── database/
│   │   │   └── session.py            # SQLAlchemy Engine, SessionLocal, Base, get_db dependency
│   │   ├── models/
│   │   │   ├── data_record.py        # DataRecordModel table definition (data_records)
│   │   │   ├── policy.py             # PolicyRuleModel table definition (retention_policies)
│   │   │   ├── audit.py              # AuditLogModel table definition (audit_logs)
│   │   │   └── __init__.py           # Model exports
│   │   ├── schemas/
│   │   │   ├── data_record.py        # Pydantic schemas for data records and AI responses
│   │   │   ├── policy.py             # Pydantic schemas for policies and evaluation items
│   │   │   ├── audit.py              # Pydantic schemas for audit log responses & filters
│   │   │   ├── action.py             # Pydantic schemas for lifecycle action requests/responses
│   │   │   └── __init__.py           # Schema exports
│   │   └── services/
│   │       ├── data_service.py       # DataRecord CRUD and query filtering
│   │       ├── ai_service.py         # Purpose mismatch semantic NLP, keyword clustering, Gemini client
│   │       ├── policy_service.py     # Retention duration parser, expiry evaluator, policy matching
│   │       ├── lifecycle_service.py  # Action executor with atomic audit logging & RBAC checks
│   │       ├── audit_service.py      # Immutable audit log creation and query retrieval
│   │       └── __init__.py           # Service exports
│   ├── tests/                        # 9 automated test suites covering all backend modules
│   ├── seed_db.py                    # SQLite database initializer and synthetic data seeder
│   └── requirements.txt              # Python dependency manifest
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx            # App chrome, dark mode toggle, backend connectivity badge
│   │   │   └── Navigation.tsx        # Persistent sidebar navigation links
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx         # Overview metrics, distribution bars, KPI tiles
│   │   │   ├── DataInventory.tsx     # Filterable data catalog table
│   │   │   ├── RecordDetails.tsx     # Single record profile lookup & AI assessment viewer
│   │   │   ├── ExpiryManagement.tsx  # 4 status lanes (Expiring Soon, Expired, Review, Completed)
│   │   │   ├── PurposeMismatch.tsx   # Purpose creep monitoring, batch audit, and sandbox
│   │   │   ├── AIInsights.tsx        # AI lifecycle insights, action cards, explanation drawer
│   │   │   ├── PolicyManagement.tsx  # [STATIC PLACEHOLDER] Needs API integration
│   │   │   └── AuditTrail.tsx        # [STATIC PLACEHOLDER] Needs API integration
│   │   ├── services/
│   │   │   └── api.ts                # Centralized Fetch API client class
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript interfaces for records, AI, health
│   │   ├── App.tsx                   # React Router DOM route declarations
│   │   └── main.tsx                  # React DOM root render
│   ├── package.json                  # Node dependency manifest
│   ├── vite.config.ts                # Vite dev server configuration and `/api` reverse proxy
│   └── tailwind.config.js            # Tailwind CSS styling configuration
│
├── data/
│   ├── synthetic/
│   │   ├── records.json              # 20 pre-generated synthetic records for seeding
│   │   └── generator.py              # CLI utility to generate 100+ synthetic records
│   └── README.md                     # Dataset documentation
│
└── docs/
    └── ARCHITECTURE.md               # Foundational architecture notes from team member 1
```

---

## 3. Detailed Data Flow & Call Sequences

### A. AI Purpose Mismatch Audit Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Privacy Officer
    participant UI as PurposeMismatch.tsx
    participant API as apiService (api.ts)
    participant Route as routes.py (/api/data/{id}/analyze)
    participant AISvc as AIService (ai_service.py)
    participant Gemini as GeminiAIProvider
    participant Google as Google Generative Language API
    participant DB as SQLite (data_records)

    User->>UI: Click "Re-Analyze Record"
    UI->>API: analyzeRecord(recordId)
    API->>Route: POST /api/data/{recordId}/analyze
    Route->>DB: Fetch record metadata by recordId
    DB-->>Route: DataRecordModel
    Route->>AISvc: analyze_record(metadata)
    
    alt Gemini API Key Configured
        AISvc->>Gemini: analyze(category, purpose, usage...)
        Gemini->>Google: POST /v1beta/models/{model}:generateContent (timeout: 6s)
        alt Success & Valid JSON
            Google-->>Gemini: 200 OK (JSON candidate)
            Gemini-->>AISvc: Parsed assessment
        else Network Timeout / HTTP Error / Non-200
            Google-->>Gemini: Timeout / 4xx / 5xx
            Gemini-->>AISvc: None (Trigger Fallback)
            AISvc->>AISvc: evaluate_purpose_compatibility() (Semantic NLP)
        end
    else No API Key Configured
        AISvc->>AISvc: evaluate_purpose_compatibility() (Semantic NLP)
    end

    AISvc-->>Route: PurposeMismatchResult
    Route->>DB: Update record (mismatch, risk_level, ai_recommendation, explanation)
    DB-->>Route: Commit & Refresh
    Route-->>API: 200 OK (PurposeMismatchResult)
    API-->>UI: Update local state & table view
    UI-->>User: Display updated risk badge & explanation
```

---

### B. Retention Policy Evaluation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Data Governance Lead
    participant UI as PolicyManagement.tsx (Target)
    participant Route as policy_routes.py (/api/policies/evaluate)
    participant PolSvc as PolicyService (policy_service.py)
    participant DB as SQLite DB

    Admin->>Route: POST /api/policies/evaluate?as_of_date=2026-10-16&expiring_soon_days=30
    Note over Route: Checks X-User-Role header (Requires ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER, AUDITOR)
    Route->>DB: Query active PolicyRuleModel records
    DB-->>Route: [POL-CUS-01, POL-TXN-01, POL-MKT-01]
    Route->>PolSvc: evaluate_all_records(db, as_of_date, expiring_soon_days)
    
    loop For each record in database
        PolSvc->>PolSvc: evaluate_expiry(expiry_date, as_of_date) -> (status, delta_days)
        PolSvc->>PolSvc: match_policy(category) -> matched_rule
        
        alt Purpose Mismatch == True
            PolSvc->>PolSvc: Deterministic Decision = REVIEW (Overrules AI)
        else Expiry Status == ACTIVE
            PolSvc->>PolSvc: Deterministic Decision = KEEP
        else Expiry Status == EXPIRING_SOON
            PolSvc->>PolSvc: Deterministic Decision = REVIEW
        else Expiry Status == EXPIRED
            PolSvc->>PolSvc: Deterministic Decision = matched_policy.action_on_expiry
        end
    end

    PolSvc-->>Route: PolicyEvaluationSummary (counts, breakdowns, record items)
    Route-->>Admin: 200 OK (JSON PolicyEvaluationSummary)
```

---

### C. Atomic Lifecycle Action Execution & Audit Trail Flow

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Governance User
    participant Route as action_routes.py (/api/data/{id}/execute-action)
    participant Security as core/security.py
    participant LifeSvc as LifecycleService
    participant AudSvc as AuditService
    participant DB as SQLite DB

    Operator->>Route: POST /api/data/CUS-1001/execute-action {"action": "ANONYMIZE", "reason": "Retention expired"}
    Note over Route: Headers: X-User-Id: officer_1, X-User-Role: PRIVACY_OFFICER
    Route->>Security: require_role([ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER])
    Security-->>Route: CurrentUser(user_id="officer_1", role="PRIVACY_OFFICER")
    Route->>LifeSvc: execute_action(db, "CUS-1001", "ANONYMIZE", "officer_1", PRIVACY_OFFICER)
    
    LifeSvc->>LifeSvc: Verify role permission (PRIVACY_OFFICER can execute REVIEW and ANONYMIZE)
    LifeSvc->>DB: Query record CUS-1001
    DB-->>LifeSvc: DataRecordModel
    
    LifeSvc->>LifeSvc: Apply state transition (status="Archived", anonymization_status="Anonymized")
    LifeSvc->>AudSvc: log_audit_event(commit=False)
    AudSvc->>DB: db.add(AuditLogModel)
    
    Note over LifeSvc,DB: Atomic Single-Transaction Commit
    LifeSvc->>DB: db.commit()
    DB-->>LifeSvc: Transaction Success
    LifeSvc->>DB: db.refresh(record), db.refresh(audit_entry)
    LifeSvc-->>Route: LifecycleActionResponse (audit_id, status, message)
    Route-->>Operator: 200 OK
```

---

## 4. Database Schema & Persistence Architecture

The system uses SQLAlchemy 2.0 ORM with declarative models located in `backend/app/models/`.

```mermaid
erDiagram
    DATA_RECORDS ||--o{ AUDIT_LOGS : "audited by record_id"
    RETENTION_POLICIES ||--o{ AUDIT_LOGS : "governed by policy_rule"

    DATA_RECORDS {
        int id PK "Autoincrement"
        string record_id UK "Unique record identifier (e.g. CUS-1001)"
        string data_type "Specific type (e.g. Customer Profile)"
        string category "Indexed category (Customer, Financial, Employee...)"
        string sensitivity "Sensitivity rating (High, Medium, Low)"
        string collection_purpose "Stated purpose at collection"
        string current_usage "Active operational usage"
        string owner "Department or owner"
        string created_date "YYYY-MM-DD"
        string retention_period "e.g. 2 years, 90 days"
        string expiry_date "YYYY-MM-DD, Indexed"
        string status "Active, Expired, Expiring Soon, Archived"
        string last_accessed "Nullable YYYY-MM-DD"
        string source "Originating system (e.g. CRM DB)"
        boolean purpose_mismatch "Usage diverges from purpose flag"
        string risk_level "Low, Medium, High, Critical"
        string ai_recommendation "KEEP, REVIEW, ANONYMIZE, DELETE"
        text ai_explanation "LLM or rule reasoning narrative"
        string policy_rule "Applied rule code"
        string review_status "Pending, In Review, Approved, Flagged"
        string anonymization_status "Not Required, Pending, Anonymized"
        string deletion_status "Not Required, Scheduled, Deleted"
        datetime created_at "UTC Timestamp"
        datetime updated_at "UTC Timestamp"
    }

    RETENTION_POLICIES {
        int id PK "Autoincrement"
        string rule_code UK "Unique policy code (e.g. POL-CUS-01)"
        string name "Descriptive name"
        string category "Category governed (or wildcard '*')"
        string retention_period "Human string (e.g. 2 years)"
        int retention_days "Computed days (e.g. 730)"
        string action_on_expiry "KEEP, REVIEW, ANONYMIZE, DELETE"
        text description "Detailed description"
        boolean is_active "Active toggle"
        datetime created_at "UTC Timestamp"
        datetime updated_at "UTC Timestamp"
    }

    AUDIT_LOGS {
        int audit_id PK "Autoincrement"
        string record_id "Record identifier affected"
        string action "KEEP, REVIEW, ANONYMIZE, DELETE, STATUS_CHANGE"
        string previous_status "Status before action"
        string new_status "Status after action"
        string user "User ID or role who executed"
        datetime timestamp "Event occurrence time"
        string reason "Compliance justification"
        string ai_recommendation "AI state at time of event"
        string policy_rule "Policy governing action"
        datetime created_at "UTC Timestamp"
    }
```

---

## 5. Authentication, RBAC, and Security Architecture

### Role-Based Access Control Structure (`backend/app/core/security.py`)

Five distinct user roles are defined:
- `ADMIN`: Unrestricted access. Can modify policies, execute all actions (including DELETE), and view audit trails.
- `DATA_GOVERNANCE`: Can configure retention policies, run evaluations, and execute actions.
- `PRIVACY_OFFICER`: Focused on compliance. Permitted to execute `REVIEW` and `ANONYMIZE`. Explicitly forbidden from executing `DELETE`.
- `AUDITOR`: Read-only compliance auditor. Can view policies, run read-only evaluations, and inspect audit logs. Forbidden from mutating records or executing actions.
- `VIEWER`: Read-only access to policies.

### Action Permissions by Role:

| Action | `ADMIN` | `DATA_GOVERNANCE` | `PRIVACY_OFFICER` | `AUDITOR` | `VIEWER` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `KEEP` | Allowed | Allowed | Denied | Denied | Denied |
| `REVIEW` | Allowed | Allowed | Allowed | Denied | Denied |
| `ANONYMIZE` | Allowed | Allowed | Allowed | Denied | Denied |
| `DELETE` | Allowed | Allowed | **Denied (403)** | Denied | Denied |

### The Critical Security Flaw (Header Extraction Fallback):
```python
def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> CurrentUser:
    user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else "local_dev_user"
    if x_user_role and x_user_role.strip():
        role = UserRole(x_user_role.strip().upper())
    else:
        role = UserRole.ADMIN  # <--- CRITICAL INSECURE DEFAULT
    return CurrentUser(user_id=user_id, role=role)
```
- **Consequence:** Requests without headers automatically receive `ADMIN` rights. Any client can spoof identity by passing arbitrary strings in `X-User-Id` and `X-User-Role`. Real authentication (JWT, OAuth2, session cookies) is completely absent.
