#!/usr/bin/env bash
# ==============================================================================
# DATAEXPIRY-AI — Environment Setup Script
# Compatible with: Linux (x86_64, aarch64, IBM Z s390x) and macOS
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================================="
echo "   DATAEXPIRY-AI — Automated Environment Setup"
echo "================================================================="
echo "Working directory: ${REPO_ROOT}"

cd "${REPO_ROOT}"

# 1. Check Python version (requires Python 3.10+)
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

PY_VERSION=$("${PYTHON_CMD}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Detected Python: ${PYTHON_CMD} (version ${PY_VERSION})"

# 2. Check Node.js and npm
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node -v)
    echo "✓ Detected Node.js: ${NODE_VERSION}"
else
    echo "⚠️ Warning: Node.js is not installed. Frontend setup will be skipped."
fi

if command -v npm >/dev/null 2>&1; then
    NPM_VERSION=$(npm -v)
    echo "✓ Detected npm: ${NPM_VERSION}"
fi

# 3. Setup Python Virtual Environment in backend/venv
echo ""
echo "📦 Setting up Python virtual environment..."
VENV_DIR="${REPO_ROOT}/backend/venv"

if [ ! -d "${VENV_DIR}" ]; then
    "${PYTHON_CMD}" -m venv "${VENV_DIR}"
    echo "✓ Created virtual environment at backend/venv"
else
    echo "✓ Existing virtual environment found at backend/venv"
fi

# Activate virtualenv
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel --quiet

# 4. Install Backend Requirements
echo ""
echo "📦 Installing backend Python dependencies..."
python -m pip install -r "${REPO_ROOT}/backend/requirements.txt"
echo "✓ Backend dependencies installed successfully"

# 5. Setup Environment Configuration (.env)
if [ ! -f "${REPO_ROOT}/.env" ]; then
    echo ""
    echo "⚙️ Creating .env configuration from .env.example..."
    cp "${REPO_ROOT}/.env.example" "${REPO_ROOT}/.env"
    echo "✓ Created .env at repository root"
else
    echo "✓ Root .env already exists"
fi

if [ ! -f "${REPO_ROOT}/backend/.env" ]; then
    cp "${REPO_ROOT}/.env.example" "${REPO_ROOT}/backend/.env"
    echo "✓ Created backend/.env"
fi

# 6. Initialize and Seed Database
echo ""
echo "🗄️ Initializing SQLite database and synthetic demo data..."
python "${REPO_ROOT}/backend/seed_db.py"

# 7. Setup Frontend Dependencies
if command -v npm >/dev/null 2>&1; then
    echo ""
    echo "📦 Installing frontend Node modules..."
    cd "${REPO_ROOT}/frontend"
    npm ci || npm install
    cd "${REPO_ROOT}"
    echo "✓ Frontend dependencies installed successfully"
fi

echo ""
echo "================================================================="
echo "✅ Setup complete! You are ready to run DATAEXPIRY-AI."
echo "   - To start backend:  ./scripts/start-backend.sh"
echo "   - To start frontend: ./scripts/start-frontend.sh"
echo "   - To run tests:      pytest backend/tests"
echo "================================================================="
