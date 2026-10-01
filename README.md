# DATAEXPIRY
### AI-Assisted Data Lifecycle & Purpose Governance Platform

![Project Status](https://img.shields.io/badge/Status-Foundation_Complete-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)
![Stack](https://img.shields.io/badge/Stack-FastAPI_%7C_React_%7C_SQLite_%7C_TypeScript-blueviolet)

---

## 📌 Problem Statement

Modern enterprises generate and store massive amounts of customer, financial, employee, and transaction data across heterogeneous databases and cloud environments. Over time, organizations face severe governance challenges:
- **Data Hoarding & Sprawl**: Storing data beyond its lawful retention period.
- **Purpose Creep**: Using data collected for one purpose (e.g. Order Processing) for unrelated secondary purposes without consent.
- **Compliance & Privacy Risks**: Violation of GDPR, CCPA, and enterprise retention compliance mandates leading to steep penalties.
- **Lack of Visibility**: Security & compliance teams lack a centralized dashboard to track data expiry, sensitivity levels, and recommended lifecycle actions.

---

## 💡 Proposed Solution

**DATAEXPIRY** is an AI-assisted data lifecycle and purpose governance platform designed to help organizations discover, monitor, evaluate, and execute automated lifecycle policies on enterprise data assets.

The system tracks every data record's lifecycle metadata:
- **What data exists**: Data Type / Category (Customer Profile, Financial Ledger, HR Record, etc.)
- **Sensitivity Level**: High, Medium, Low
- **Collection Purpose**: Why the data was originally gathered
- **Current Usage**: How the data is being actively used
- **Retention & Expiry**: Created date, retention period, exact expiry date, lifecycle status
- **Automated Lifecycle Recommendations**: `KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`

---

## ✨ Main Features (Platform Roadmap)

- 📊 **Centralized Data Inventory**: Real-time catalog of enterprise data records and metadata.
- ⏳ **Expiry & Retention Management**: Track expired and expiring-soon records automatically.
- 🎯 **Purpose Mismatch Detection**: Identify when current usage diverges from collection purpose *(Module for Team Member 2)*.
- 🤖 **AI Lifecycle Insights**: LLM-driven risk scoring, lifecycle recommendations, and clear explanations *(Module for Team Member 2)*.
- 🛡️ **Policy Engine & Action Execution**: Enforce retention rules and trigger anonymization or deletion flows *(Module for Team Member 4)*.
- 📜 **Immutable Audit Trail**: Log all lifecycle events, policy changes, and data actions for compliance compliance *(Module for Team Member 4)*.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Icons & UI**: Lucide React
- **HTTP Client**: Centralized Fetch API Service

### Backend
- **Framework**: Python 3.10+ with FastAPI
- **ORM & DB**: SQLAlchemy 2.0 (SQLite for initial local dev, PostgreSQL-ready)
- **Validation**: Pydantic v2
- **Testing**: Pytest & HTTPX

---

## 🏗️ Architecture & Project Structure

```
DataExpiry/
│
├── backend/                  # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py           # FastAPI Application Entrypoint & CORS setup
│   │   ├── api/              # API Route Handlers
│   │   │   └── routes.py     # Endpoints (Health, Data Records)
│   │   ├── models/           # SQLAlchemy Database Models
│   │   │   └── data_record.py # Enterprise Data Record Schema
│   │   ├── schemas/          # Pydantic Request/Response Schemas
│   │   │   └── data_record.py
│   │   ├── services/         # Business Logic Layer
│   │   │   └── data_service.py
│   │   ├── database/         # DB Connection & Session Management
│   │   │   └── session.py
│   │   └── core/             # Configuration & Environment Variables
│   │       └── config.py
│   ├── tests/                # Automated Pytest Suite
│   │   ├── test_api.py
│   │   └── test_db.py
│   ├── seed_db.py            # Database Initialization & Seeding Script
│   ├── requirements.txt      # Python Dependencies
│   └── .env.example          # Environment Variable Blueprint
│
├── frontend/                 # React + TypeScript + Vite Frontend
│   ├── src/
│   │   ├── components/       # Reusable Navigation & Layout Components
│   │   ├── pages/            # View Pages (Dashboard, Inventory, AI Insights, etc.)
│   │   ├── services/         # Centralized API Service Layer (api.ts)
│   │   ├── types/            # TypeScript Interfaces
│   │   ├── App.tsx           # Router Setup
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── data/
│   ├── synthetic/
│   │   ├── records.json      # Initial Synthetic Data (20+ records)
│   │   └── generator.py      # Seed Data Generator Script
│   └── README.md             # Dataset documentation
│
├── docs/                     # Architecture & Integration Guides
│   └── ARCHITECTURE.md
│
├── .gitignore                # Excludes secrets, node_modules, venvs, DBs
├── README.md                 # Project Overview & Setup Guide
└── LICENSE                   # MIT License
```

---

## 👥 Team Structure & Responsibilities

| Role | Developer | Responsibilities & Focus Area | Branch |
| :--- | :--- | :--- | :--- |
| **Person 1** | **Foundation Lead** | Project structure, DB schema, FastAPI foundation, Synthetic dataset, Frontend shell & API service | `feature/person1-foundation` |
| **Person 2** | **AI & Insights Lead** | Purpose mismatch engine, AI risk analyzer, LLM integration, recommendation generator | `feature/person2-ai` |
| **Person 3** | **Frontend & UX Lead** | Interactive dashboard, rich data tables, record detail modal, expiry management UI | `feature/person3-frontend` |
| **Person 4** | **Policy & Audit Lead** | Policy rules engine, automated anonymization/deletion workflows, compliance audit log | `feature/person4-policy-audit` |

---

## 🌿 Git Branching & Collaboration Workflow

To ensure seamless collaboration without merge conflicts:

1. **`main`**: Production-ready code. Protected branch.
2. **`develop`**: Integration branch for feature testing.
3. **Feature Branches**:
   - `feature/person1-foundation` (Current)
   - `feature/person2-ai`
   - `feature/person3-frontend`
   - `feature/person4-policy-audit`

### Commit & PR Instructions:
- Always branch off `develop`: `git checkout -b feature/your-feature-name develop`
- Pull latest changes before pushing: `git pull origin develop`
- Create PRs targeted to `develop`.

---

## 🚀 Local Setup & Getting Started

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm
- Git

---

### 1️⃣ Backend Setup (FastAPI + SQLite)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration file
cp .env.example .env

# Initialize database and seed synthetic records
python seed_db.py

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

The API server will run at: **`http://localhost:8000`**
Interactive Swagger Documentation: **`http://localhost:8000/docs`**

---

### 2️⃣ Frontend Setup (React + Vite + Tailwind)

```bash
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```

The React application will run at: **`http://localhost:5173`**

---

## 🗄️ Database Architecture

The platform uses **SQLAlchemy ORM** to abstract database operations:
- **Local Development**: SQLite (`sqlite:///./dataexpiry.db`)
- **Production Ready**: Easily switches to PostgreSQL by changing `DATABASE_URL` in `.env` (e.g. `postgresql://user:password@localhost:5432/dataexpiry`).

### Schema Overview (`data_records`)
- `id` (Primary Key, Integer)
- `record_id` (Unique Identifier, e.g. `CUS-1001`)
- `data_type`, `category`, `sensitivity`
- `collection_purpose`, `current_usage`, `owner`
- `created_date`, `retention_period`, `expiry_date`, `status`
- `last_accessed`, `source`, `created_at`, `updated_at`
- **Future-compatible extension fields**: `purpose_mismatch`, `risk_level`, `ai_recommendation`, `ai_explanation`, `policy_rule`, `review_status`, `anonymization_status`, `deletion_status`.

---

## 🧪 Running Tests

```bash
# From backend directory with venv activated
pytest
```

---

## 🔮 Future Enhancements & Deployment Note

- **LinuxONE Deployment**: Prepared for containerized deployment (Docker file structure included). Enterprise deployment will be evaluated in upcoming phases.
- **Real-time Event Streaming**: Webhooks for automated retention enforcement.
- **Enterprise DB Connectors**: Integration drivers for PostgreSQL, MySQL, and Snowflake.
