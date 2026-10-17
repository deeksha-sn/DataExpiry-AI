# DATAEXPIRY-AI — Architectural Blueprint & System Design

## 1. System Overview

**DATAEXPIRY-AI** is a cloud-native, AI-assisted enterprise data lifecycle and purpose governance platform. Modern enterprises collect vast amounts of sensitive customer, financial, HR, and transaction data across heterogeneous databases. Over time, organizations face severe governance challenges:
- **Data Hoarding:** Storing records beyond their statutory retention periods.
- **Purpose Creep:** Using data collected for one purpose (e.g. Order Fulfillment) for unauthorized secondary activities (e.g. Third-Party Targeted Marketing or AI model training).
- **Compliance Penalties:** Violations of GDPR (Articles 5, 17), CCPA, and enterprise retention mandates.

DATAEXPIRY-AI provides automated retention tracking, semantic drift detection between stated collection purposes and active data usage, deterministic policy evaluation, simulated lifecycle action execution (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`), and an immutable audit trail.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Client Layer (React 18 + TypeScript + Vite)"]
        UI_Dash["Dashboard<br>(KPIs & Metrics)"]
        UI_Inv["Data Inventory<br>(Search & Filters)"]
        UI_Exp["Expiry Management<br>(Prioritized Queues)"]
        UI_Sand["Purpose Sandbox<br>(Interactive Testing)"]
        UI_Pol["Policy Management<br>(CRUD & Evaluation)"]
        UI_Aud["Audit Trail Viewer<br>(Compliance Logs)"]
    end

    subgraph ApiGateway["FastAPI Gateway (/api)"]
        MW_CORS["CORS Middleware"]
        MW_Auth["RBAC Dependency<br>(require_role / get_current_user)"]
        R_Data["Data & Action Routes<br>(/api/data)"]
        R_AI["AI Governance Routes<br>(/api/ai)"]
        R_Pol["Policy Routes<br>(/api/policies)"]
        R_Aud["Audit Routes<br>(/api/audit)"]
    end

    subgraph ServiceLayer["Business Logic Layer"]
        S_Data["DataRecordService<br>(Query & Catalog Operations)"]
        S_Policy["PolicyService<br>(Duration Parsing & Evaluation)"]
        S_Life["LifecycleService<br>(Deterministic State Transitions)"]
        S_Audit["AuditService<br>(Immutable Event Logging)"]
        S_AI["AIService (Hybrid NLP Engine)<br>├── Cache & Deduplication<br>├── Rate Limiter (10 RPM)<br>└── Rule-Based Domain Fallback"]
    end

    subgraph ExternalServices["External LLM Integration"]
        Gemini["Google Gemini REST API<br>(gemini-3.5-flash-lite)<br>Strict Privacy Boundary (No PII)"]
    end

    subgraph PersistenceLayer["Data Persistence (SQLAlchemy 2.0 ORM)"]
        DB_Records[("data_records<br>(24 columns)")]
        DB_Policies[("retention_policies<br>(11 columns)")]
        DB_Audit[("audit_logs<br>(11 columns)")]
    end

    ClientLayer -->|HTTP REST / JSON| ApiGateway
    ApiGateway --> ServiceLayer
    S_AI -.->|Sanitized Metadata Only| ExternalServices
    ServiceLayer --> PersistenceLayer
```

---

## 3. Layered Design Principles

### A. Presentation Layer (Frontend)
- **Framework:** React 18 with TypeScript.
- **Styling:** Tailwind CSS with responsive dark/light theme support.
- **API Client:** Centralized [`apiService`](../frontend/src/services/api.ts) with typed response models, centralized error handling (`parseError`), and configurable development identity headers.

### B. Application Gateway Layer (FastAPI)
- **FastAPI Core:** Declarative routing, automatic OpenAPI 3.0 documentation (`/docs`), Pydantic v2 request/response schema validation.
- **Fail-Closed RBAC:** Dependency injection factory `require_role(...)` enforces least-privilege role verification before endpoint logic execution.

### C. Domain Services Layer
- **`DataRecordService`:** Handles CRUD and case-insensitive search across data assets.
- **`PolicyService`:** Parses human duration strings (`"2 years"` -> `730 days`) using regular expressions and matches records against category policies.
- **`LifecycleService`:** Manages deterministic lifecycle state transitions and coordinates atomic audit logging.
- **`AuditService`:** Records append-only compliance logs within the same database transaction.
- **`AIService`:** Hybrid engine combining Google Gemini with an offline, deterministic semantic analyzer.

### D. Persistence Layer (SQLAlchemy 2.0)
- **Development Database:** SQLite with thread-safe connection pooling.
- **Production Readiness:** Direct compatibility with PostgreSQL via the `DATABASE_URL` environment variable.
