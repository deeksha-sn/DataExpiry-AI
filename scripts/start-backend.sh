#!/usr/bin/env bash
# ==============================================================================
# DATAEXPIRY-AI — Backend Startup Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VENV_DIR="${REPO_ROOT}/backend/venv"

if [ ! -d "${VENV_DIR}" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first."
    exit 1
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

cd "${REPO_ROOT}/backend"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "🚀 Starting DATAEXPIRY FastAPI backend server on http://${HOST}:${PORT}..."
echo "📚 Interactive API documentation will be available at http://${HOST}:${PORT}/docs"

exec python -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
