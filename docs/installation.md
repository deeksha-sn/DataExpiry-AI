# Local Installation & Quickstart Guide

This guide covers local environment setup, configuration, and verification for **DATAEXPIRY-AI** on Linux, macOS, and Windows.

---

## 1. Prerequisites

Before installing, ensure the following tools are available on your system:

| Dependency | Minimum Version | Recommended Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | 3.11 or 3.12 | `python3 --version` |
| **Node.js** | 18 LTS | 20 LTS | `node -v` |
| **npm** | 9+ | 10+ | `npm -v` |
| **Git** | 2.30+ | Latest | `git --version` |

---

## 2. Automated Installation (Linux / macOS / WSL)

The repository provides an automated installation script that checks prerequisites, sets up virtual environments, installs Python/Node dependencies, and seeds sample data:

```bash
# Clone the repository
git clone https://github.com/your-org/DATAEXPIRY-AI.git
cd DATAEXPIRY-AI

# Run automated setup
chmod +x scripts/*.sh
./scripts/setup.sh
```

---

## 3. Manual Step-by-Step Installation

### Step A: Configure Environment Variables
Copy `.env.example` to `.env` in the repository root:
```bash
cp .env.example .env
```

### Step B: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Initialize database tables and seed synthetic data
python seed_db.py

# Verify backend tests pass
pytest
```

### Step C: Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies cleanly
npm ci

# Verify TypeScript typechecking
npm run lint

# Build production bundle
npm run build
```

---

## 4. Starting the Development Servers

### Option A: Using Startup Scripts (Linux / macOS)
```bash
# Start FastAPI backend (Terminal 1)
./scripts/start-backend.sh

# Start Vite frontend (Terminal 2)
./scripts/start-frontend.sh
```

### Option B: Manual Execution
**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

---

## 5. Verifying the Installation

1. **Backend Health Check:**
   Open [http://localhost:8000/api/health](http://localhost:8000/api/health) in your browser. Expected response:
   ```json
   {
     "status": "ok",
     "service": "DATAEXPIRY API",
     "version": "1.0.0"
   }
   ```
2. **Interactive API Documentation:**
   Explore Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).
3. **Frontend Application:**
   Navigate to [http://localhost:5173](http://localhost:5173). The top navbar should display a green `Backend API: connected` status badge.
