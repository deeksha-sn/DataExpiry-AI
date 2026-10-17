#!/usr/bin/env bash
# ==============================================================================
# DATAEXPIRY-AI — Frontend Startup Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

FRONTEND_DIR="${REPO_ROOT}/frontend"

if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo "❌ Frontend node_modules not found. Please run ./scripts/setup.sh first."
    exit 1
fi

cd "${FRONTEND_DIR}"

HOST="${FRONTEND_HOST:-0.0.0.0}"
PORT="${FRONTEND_PORT:-5173}"

echo "🌐 Starting DATAEXPIRY React + Vite frontend development server on http://${HOST}:${PORT}..."

exec npm run dev -- --host "${HOST}" --port "${PORT}"
