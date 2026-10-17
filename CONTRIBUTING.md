# Contributing to DATAEXPIRY-AI

Thank you for your interest in contributing to **DATAEXPIRY-AI**! This platform provides an AI-assisted enterprise data lifecycle and purpose governance solution.

---

## 🌿 Git Branching & Workflow

We follow standard feature-branch workflows:

1. **`main`**: Protected, production-ready branch.
2. **`develop`**: Integration branch for ongoing sprint features.
3. **`feature/*`**: Feature branches branched from `develop`:
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

---

## 🛠️ Local Development Setup

### 1. Backend Setup (FastAPI)
```bash
cd backend
python3 -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
python seed_db.py
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Verification Standards

All contributions must pass automated tests, linting, and build validation before a pull request can be merged:

1. **Backend Tests:**
   ```bash
   pytest backend/tests
   ```
   *Requirement: 100% pass rate across all unit and integration tests.*

2. **Frontend Type-Checking & Linting:**
   ```bash
   cd frontend
   npm run lint
   ```

3. **Frontend Production Build:**
   ```bash
   cd frontend
   npm run build
   ```

---

## 🔒 Security & RBAC Guidelines

- **Never Commit Secrets:** Do not commit `.env`, API keys, private keys, or passwords.
- **Fail-Closed RBAC:** All privileged actions must be gated by `require_role(...)`. Never bypass authentication checks or set `ALLOW_DEV_HEADER_AUTH=True` in production code.
- **Privacy Boundary for External AI:** Never send PII (names, emails, record IDs) to external LLM providers. Always preserve the offline deterministic fallback.

---

## 📜 Pull Request Checklist

- [ ] Branch is rebased onto latest `develop`.
- [ ] Automated tests pass (`pytest backend/tests`).
- [ ] Frontend builds without TypeScript or bundling errors (`npm run build`).
- [ ] No database files (`*.db`), secrets, or unnecessary artifacts are committed.
- [ ] Documentation is updated in `docs/` where applicable.
