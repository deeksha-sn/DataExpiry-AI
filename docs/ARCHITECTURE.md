# DATAEXPIRY Architecture & Technical Blueprint

This document outlines the architectural foundation, component boundaries, database design, and integration guidelines for the DATAEXPIRY platform.

---

## 🏛️ System Architecture Overview

DATAEXPIRY follows a modular three-tier architecture:

```
[ Frontend: React + TypeScript + Vite ]
                   │
                   │  HTTP REST (JSON) / CORS Enabled
                   ▼
[ Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.0 ]
         │                        │
         │ (SQLAlchemy ORM)       │ (Pluggable Provider)
         ▼                        ▼
[ SQLite / PostgreSQL ]    [ AI & Policy Modules (Team 2 & 4) ]
```

---

## 🗄️ Database Design (`data_records`)

### Table Schema Definition

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Autoincrement | Internal DB primary key |
| `record_id` | String(50) | Unique, Indexed, Not Null | Public record identifier (e.g. `CUS-1001`) |
| `data_type` | String(100) | Not Null | Specific type of data (e.g. `Customer Profile`, `Payroll Data`) |
| `category` | String(50) | Not Null, Indexed | Broad category (`Customer`, `Financial`, `Employee`, `Identity`, `Transaction`) |
| `sensitivity` | String(20) | Not Null | Data sensitivity (`High`, `Medium`, `Low`) |
| `collection_purpose` | String(255) | Not Null | Purpose stated at collection time |
| `current_usage` | String(255) | Not Null | How the data is currently being utilized |
| `owner` | String(100) | Not Null | Data owner / department (e.g. `Finance Dept`, `HR Operations`) |
| `created_date` | String(20) | Not Null | Date when record was originally created (`YYYY-MM-DD`) |
| `retention_period` | String(50) | Not Null | Mandated retention period (e.g. `2 years`, `5 years`, `90 days`) |
| `expiry_date` | String(20) | Not Null, Indexed | Date when retention expires (`YYYY-MM-DD`) |
| `status` | String(30) | Not Null, Indexed | Lifecycle status (`Active`, `Expired`, `Expiring Soon`, `Archived`) |
| `last_accessed` | String(20) | Nullable | Date of last access or query |
| `source` | String(100) | Not Null | Source system (e.g. `CRM DB`, `Billing Portal`, `Identity Store`) |
| `created_at` | DateTime | Default UTC now | System creation timestamp |
| `updated_at` | DateTime | Default UTC now, On update | System modification timestamp |

### Future Extension Fields (Reserved for Team 2 & 4)

| Column Name | Data Type | Default | Owner / Module |
| :--- | :--- | :--- | :--- |
| `purpose_mismatch` | Boolean | `False` | Team Member 2 (AI Mismatch Engine) |
| `risk_level` | String(20) | `Low` | Team Member 2 (AI Risk Analyzer) |
| `ai_recommendation` | String(20) | `KEEP` | Team Member 2 (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`) |
| `ai_explanation` | Text | `None` | Team Member 2 (LLM Reasoning Text) |
| `policy_rule` | String(100) | `None` | Team Member 4 (Policy Governance Engine) |
| `review_status` | String(30) | `Pending` | Team Member 4 (`Pending`, `In Review`, `Approved`, `Flagged`) |
| `anonymization_status` | String(30) | `Not Required` | Team Member 4 (`Not Required`, `Pending`, `Anonymized`) |
| `deletion_status` | String(30) | `Not Required` | Team Member 4 (`Not Required`, `Scheduled`, `Deleted`) |

---

## 🔌 API Endpoints (Foundation v1.0)

All backend endpoints are prefixed with `/api` and accept/return JSON.

| Method | Path | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root API welcome message & version | None |
| `GET` | `/api/health` | Healthcheck endpoint | None |
| `GET` | `/api/data` | Fetch data records | `category`, `status`, `sensitivity`, `limit`, `offset` |
| `GET` | `/api/data/{record_id}` | Fetch single record details | Path param `record_id` |
| `POST` | `/api/data` | Create a new data record | JSON Body (`DataRecordCreate`) |

---

## 🚀 Module Integration Points for Team Members

### 🧠 Team Member 2 — AI & Purpose Mismatch Engine
- Target directory: `backend/app/services/ai_service.py` (to be added)
- Target endpoints: `POST /api/data/{record_id}/analyze` or `POST /api/ai/batch-analyze`
- Responsibilities: Populates `purpose_mismatch`, `risk_level`, `ai_recommendation`, and `ai_explanation`.

### 🎨 Team Member 3 — Frontend & UI Enhancements
- Target directory: `frontend/src/pages/`
- Target service: Extend `frontend/src/services/api.ts` with new API methods.
- Responsibilities: Implement rich table controls, interactive filtering, modal views, and visually appealing cards.

### 🛡️ Team Member 4 — Policy Engine & Audit Logging
- Target directory: `backend/app/services/policy_service.py` and `backend/app/models/audit.py` (to be added)
- Target endpoints: `GET /api/policies`, `POST /api/data/{record_id}/execute-action`
- Responsibilities: Implement rules evaluation, lifecycle actions (`ANONYMIZE`, `DELETE`), and immutable audit event logs.
