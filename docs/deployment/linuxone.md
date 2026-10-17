# IBM LinuxONE (s390x) Deployment Guide

This guide provides step-by-step instructions for deploying and running **DATAEXPIRY-AI** on the **IBM LinuxONE Community Cloud** running IBM Z architecture (`s390x`) with **Python 3.12.3**.

---

## 1. System Overview & Architecture Compatibility

- **Host Architecture:** IBM Z / LinuxONE (`s390x`)
- **Operating Systems Tested:** Ubuntu 22.04 LTS / 24.04 LTS (`s390x`), RHEL 9 (`s390x`), SLES 15 (`s390x`)
- **Default Deployment Directory:** `/home/linux1/datathon_project/DataExpiry-AI`
- **Default Service Ports:**
  - FastAPI Backend: `8000`
  - Vite Frontend: `5173` (or port `80`/`443` via Nginx)

### s390x Native Compilation Considerations
While most Python packages on PyPI are pure Python and install immediately, some packages include native C or Rust extensions:
- **`pydantic-core`:** PyPI provides manylinux `s390x` wheels for Pydantic v2.6+. If building from source on non-standard distributions, ensure `rustc` and `cargo` are installed.
- **`greenlet` (SQLAlchemy ORM dependency):** May compile from source during `pip install`. Requires `gcc`, `make`, and `python3-dev`.
- **`sqlite3`:** Bundled directly in standard Linux Python binaries. Zero external compilation required.
- **`psycopg2` (Optional for PostgreSQL):** If switching from SQLite to PostgreSQL on `s390x`, install `libpq-dev` (Ubuntu) or `postgresql-devel` (RHEL) so `psycopg2` can compile native bindings.

---

## 2. Prerequisites & System Packages

Log in to your IBM LinuxONE virtual instance via SSH:
```bash
ssh linux1@<your-linuxone-ip>
```

### Ubuntu / Debian (s390x)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    gcc \
    git \
    curl \
    nodejs \
    npm
```

### RHEL / Rocky Linux (s390x)
```bash
sudo dnf update -y
sudo dnf install -y \
    python3 \
    python3-devel \
    python3-pip \
    gcc \
    make \
    git \
    curl \
    nodejs \
    npm
```

Verify installed versions on `s390x`:
```bash
uname -m          # Output must be: s390x
python3 --version # Output: Python 3.12.x or 3.10+
node -v           # Output: v18.x.x or v20.x.x
npm -v            # Output: 9.x.x+
```

---

## 3. Clone & Project Directory Setup

Set up the project in the recommended deployment directory:
```bash
mkdir -p /home/linux1/datathon_project
cd /home/linux1/datathon_project

# Clone the repository
git clone https://github.com/your-org/DATAEXPIRY-AI.git DataExpiry-AI
cd DataExpiry-AI
```

---

## 4. Automated Setup

Run the included automated setup script:
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

The script will automatically:
1. Create a Python virtual environment at `backend/venv`.
2. Upgrade `pip`, `setuptools`, and `wheel`.
3. Install all backend dependencies from `backend/requirements.txt`.
4. Copy `.env.example` to `.env` (if not already present).
5. Initialize the SQLite database and seed 20 demonstration records.
6. Install frontend npm dependencies via `npm ci`.

---

## 5. Manual Setup (Alternative)

If you prefer to execute each step manually on LinuxONE:

### Step 1: Backend Setup
```bash
cd /home/linux1/datathon_project/DataExpiry-AI/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade wheel and pip
pip install --upgrade pip setuptools wheel

# Install backend dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Initialize and seed database
python seed_db.py

# Verify backend test suite (122 tests)
pytest tests/
```

### Step 2: Frontend Setup
```bash
cd /home/linux1/datathon_project/DataExpiry-AI/frontend

# Install dependencies cleanly
npm ci

# Verify TypeScript typecheck
npm run lint

# Build production bundle
npm run build
```

---

## 6. Running the Services on LinuxONE

### Starting the Backend
```bash
cd /home/linux1/datathon_project/DataExpiry-AI
./scripts/start-backend.sh
```
Or with direct Uvicorn execution:
```bash
cd /home/linux1/datathon_project/DataExpiry-AI/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Starting the Frontend
In a separate terminal or tmux session:
```bash
cd /home/linux1/datathon_project/DataExpiry-AI
./scripts/start-frontend.sh
```

---

## 7. Verifying Deployment Health

From the LinuxONE terminal or a remote client:
```bash
# Verify Healthcheck Endpoint
curl -s http://localhost:8000/api/health | jq .
```
Expected output:
```json
{
  "status": "ok",
  "service": "DATAEXPIRY API",
  "version": "1.0.0"
}
```

```bash
# Query Catalog Records
curl -s http://localhost:8000/api/data?limit=2 | jq .
```

---

## 8. Production Daemonization (Systemd Service Templates)

For persistent background execution on LinuxONE, create systemd services:

### Backend Service: `/etc/systemd/system/dataexpiry-backend.service`
```ini
[Unit]
Description=DATAEXPIRY FastAPI Backend Service (IBM LinuxONE)
After=network.target

[Service]
Type=simple
User=linux1
WorkingDirectory=/home/linux1/datathon_project/DataExpiry-AI/backend
ExecStart=/home/linux1/datathon_project/DataExpiry-AI/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ENVIRONMENT=production
Environment=ALLOW_DEV_HEADER_AUTH=false

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dataexpiry-backend
sudo systemctl start dataexpiry-backend
sudo systemctl status dataexpiry-backend
```

---

## 9. Nginx Reverse Proxy Configuration (Optional)

To serve the frontend and backend together on port 80:

```nginx
server {
    listen 80;
    server_name _;

    # Serve compiled React frontend
    location / {
        root /home/linux1/datathon_project/DataExpiry-AI/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy Swagger docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
```

---

## 10. Troubleshooting LinuxONE (s390x) Issues

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `error: command 'gcc' failed` during `pip install` | Missing C compiler on LinuxONE | Run `sudo apt install -y build-essential gcc python3-dev` |
| `pip install greenlet` fails | Missing Python header files | Ensure `python3-dev` (Ubuntu) or `python3-devel` (RHEL) is installed |
| `npm: command not found` | Node.js not installed | Install Node 18 or 20 via distribution package manager or NodeSource |
| Port 8000 unreachable remotely | Cloud firewall / Security group | Open port 8000 and 5173 in the IBM Cloud / LinuxONE security group |
| Backend tests fail on dev headers | Header auth disabled in prod | Tests automatically set `ENVIRONMENT=development` and `ALLOW_DEV_HEADER_AUTH=True` in test fixtures |
