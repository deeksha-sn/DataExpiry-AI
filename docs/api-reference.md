# DATAEXPIRY-AI — API Reference & Specification

All backend endpoints are served under the `/api` prefix and accept/return JSON payloads. Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 1. System & Health Endpoints

### `GET /`
- **Description:** Root welcome message and API metadata.
- **Auth:** None (Public).
- **Response (200 OK):**
  ```json
  {
    "service": "DATAEXPIRY API",
    "version": "1.0.0",
    "status": "online",
    "documentation": "/docs"
  }
  ```

### `GET /api/health`
- **Description:** System health check endpoint polled by frontend navigation.
- **Auth:** None (Public).
- **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "service": "DATAEXPIRY API",
    "version": "1.0.0"
  }
  ```

---

## 2. Enterprise Data Catalog Endpoints

### `GET /api/data`
- **Description:** List enterprise data records with optional query filtering and pagination.
- **Query Parameters:**
  - `category` (optional, string): Case-insensitive category filter (`Customer`, `Financial`, `Employee`, `Identity`, `Transaction`).
  - `status` (optional, string): Lifecycle status (`Active`, `Expired`, `Expiring Soon`, `Archived`).
  - `sensitivity` (optional, string): Sensitivity classification (`High`, `Medium`, `Low`).
  - `limit` (optional, integer, default: 100, max: 500): Page limit.
  - `offset` (optional, integer, default: 0): Pagination offset.
- **Response (200 OK):** `Array<DataRecordResponse>`

### `GET /api/data/{record_id}`
- **Description:** Fetch single data record by public identifier (e.g. `CUS-1001`) or internal numeric ID.
- **Response (200 OK):** `DataRecordResponse`
- **Response (404 Not Found):** `{"detail": "Data record '...' not found."}`

### `POST /api/data`
- **Description:** Register a new data asset in the governance catalog.
- **Request Body (`DataRecordCreate`):**
  ```json
  {
    "record_id": "CUS-2001",
    "data_type": "Customer Contact",
    "category": "Customer",
    "sensitivity": "High",
    "collection_purpose": "Order Delivery",
    "current_usage": "Order Delivery",
    "owner": "Customer Care",
    "created_date": "2024-01-01",
    "retention_period": "2 years",
    "expiry_date": "2026-01-01",
    "status": "Active",
    "source": "CRM Database"
  }
  ```
- **Response (201 Created):** `DataRecordResponse`
- **Response (400 Bad Request):** Record identifier already exists.

---

## 3. AI Governance & Purpose Mismatch Endpoints

### `POST /api/ai/batch-analyze`
- **Description:** Triggers automated purpose mismatch analysis across all records in the database.
- **Response (200 OK):** `BatchAIAnalysisResponse` with summary distributions and record-by-record analysis.

### `POST /api/data/{record_id}/analyze`
- **Description:** Executes AI analysis for a specific record and updates its governance attributes in the database.
- **Response (200 OK):** `PurposeMismatchResult`

### `POST /api/ai/check-mismatch`
- **Description:** Interactive sandbox for testing purpose compatibility without modifying database state.
- **Request Body (`PurposeMismatchCheckRequest`):**
  ```json
  {
    "collection_purpose": "Account Management",
    "current_usage": "Targeted Marketing Campaigns",
    "category": "Customer",
    "sensitivity": "High"
  }
  ```
- **Response (200 OK):** `PurposeMismatchResult` (`purpose_mismatch: true`, `risk_level: "High"`, `ai_recommendation: "REVIEW"`, `explanation: "..."`)

### `GET /api/ai/summary`
- **Description:** Returns aggregate governance metrics, mismatch drift counts, risk distributions, and recommendation counts.

---

## 4. Retention Policy Endpoints

### `GET /api/policies`
- **Description:** List retention policy rules (`active_only` optional query parameter).
- **Auth Roles:** `ADMIN`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`, `AUDITOR`, `VIEWER`.
- **Response (200 OK):** `Array<PolicyRuleResponse>`

### `POST /api/policies`
- **Description:** Create a new retention policy.
- **Auth Roles:** `ADMIN`, `DATA_GOVERNANCE`.
- **Request Body (`PolicyRuleCreate`):**
  ```json
  {
    "rule_code": "POL-HR-01",
    "name": "Employee Record Retention",
    "category": "Employee",
    "retention_period": "5 years",
    "action_on_expiry": "REVIEW",
    "description": "Statutory 5-year retention for personnel files"
  }
  ```
- **Response (201 Created):** `PolicyRuleResponse`

### `PUT /api/policies/{id}`
- **Description:** Update an existing policy rule.
- **Auth Roles:** `ADMIN`, `DATA_GOVERNANCE`.

### `DELETE /api/policies/{id}`
- **Description:** Soft-deactivate a policy rule (`is_active = False`).
- **Auth Roles:** `ADMIN`, `DATA_GOVERNANCE`.

### `POST /api/policies/evaluate`
- **Description:** Batch evaluate all catalog records against active policies as of a specified date.
- **Auth Roles:** `ADMIN`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`, `AUDITOR`.

---

## 5. Audit Trail & Action Execution Endpoints

### `GET /api/audit`
- **Description:** Retrieve chronological compliance audit trail with filtering (`record_id`, `action`, `user`, `limit`, `offset`).
- **Auth Roles:** `ADMIN`, `AUDITOR`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`.

### `GET /api/audit/{record_id}`
- **Description:** Retrieve full chronological audit history for a specific record.
- **Auth Roles:** `ADMIN`, `AUDITOR`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`.

### `POST /api/data/{record_id}/execute-action`
- **Description:** Execute a deterministic lifecycle action on a record (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`).
- **Auth Roles:**
  - `DELETE`: `ADMIN`, `DATA_GOVERNANCE` only.
  - `ANONYMIZE`: `ADMIN`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER` only.
  - `REVIEW`: `ADMIN`, `DATA_GOVERNANCE`, `PRIVACY_OFFICER`.
  - `KEEP`: `ADMIN`, `DATA_GOVERNANCE`.
  - `VIEWER`, `AUDITOR`: Denied (403 Forbidden).
- **Request Body (`LifecycleActionRequest`):**
  ```json
  {
    "action": "ANONYMIZE",
    "reason": "Retention expired; de-identifying per compliance policy"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "record_id": "CUS-1001",
    "action_executed": "ANONYMIZE",
    "previous_status": "Expired",
    "new_status": "Archived",
    "audit_id": 42,
    "message": "Record 'CUS-1001' marked as Anonymized and Archived.",
    "deletion_status": "Not Required",
    "anonymization_status": "Anonymized",
    "review_status": "Pending"
  }
  ```
