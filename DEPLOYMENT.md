# IncentiveHouse ERP — Deployment Guide

## Prerequisites

- Python 3.13+
- SQL Server instance with ODBC Driver 17+ or 18
- ODBC Driver: "ODBC Driver 18 for SQL Server" (Windows) or `msodbcsql18` (Linux)

## Quick Start (Development)

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure .env (copy from template, edit credentials)
copy .env.template .env  # Windows
cp .env.template .env    # Linux

# 4. Run
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
```

## Production Checklist

- [ ] **Generate strong JWT_SECRET**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **Set strong ADMIN_PASSWORD** in `.env` (min 12 chars, mixed case + digits)
- [ ] **Restrict CORS_ORIGINS** to actual frontend domain(s), not `*`
- [ ] **Set DEBUG=false** and **LOG_LEVEL=INFO** or `WARNING`
- [ ] **Configure SSL**: set `SSL_CERTFILE` and `SSL_KEYFILE` in `.env`, or use reverse proxy (nginx/Caddy)
- [ ] **Run behind reverse proxy** (recommended): nginx → uvicorn on localhost:9001
- [ ] **Enable connection pooling**: tune `SQLALCHEMY_POOL_SIZE` / `SQLALCHEMY_MAX_OVERFLOW` in database.py
- [ ] **Schedule DB backups** for `IHE_ERP` database
- [ ] **Create SQL Server login** with minimum required permissions (not `sa`)
- [ ] **Run database DDL scripts**: `07_Neural_AI_Tables.sql`, `08_Document_System.sql`
- [ ] **Disable `/docs` (Swagger UI)** in production if not needed: `app = FastAPI(docs_url=None)`
- [ ] **Monitor logs** — stderr/stdout are captured by systemd/supervisor/Docker

## Real ML Models (P6)

When SQL Server data is available, train production models:

```bash
pip install -r requirements_p6.txt

# Train all models from historical data
python -c "
from app.neural.models.cashflow import CashflowPredictor
from app.neural.models.churn import ChurnPredictor
from app.neural.models.overrun import OverrunPredictor
from app.neural.models.anomaly import AnomalyDetector
from app.neural.models.registry import ModelRegistry

reg = ModelRegistry()
# Each model loads data via SQL queries, trains, and saves to data/models/
print('Models ready for training — run app/neural/train.py')
"
```

Model files are persisted in `data/models/` as pickle + JSON metadata, served by `ModelRegistry`.

## CI/CD Pipeline (P7)

```yaml
# .github/workflows/ci.yml
# Triggers: push to main/develop, PR to main
# Services: SQL Server 2022 Express (Docker sidecar)
# Steps: install ODBC → deps → DDL → migrations → pytest → ruff lint
```

### Status Badge

```markdown
[![CI](https://github.com/YOUR_ORG/IHE-ERP/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/IHE-ERP/actions/workflows/ci.yml)
```

To enable: push to GitHub → Actions tab → the workflow runs automatically.

## Production Hardening (P5)

### Structured Logging

All logs emit JSON to stdout and a rotating file (`data/logs/ihe-erp.log`, 10 MB × 5 backups):

```json
{"timestamp": "2026-06-05T12:30:00+00:00", "level": "INFO", "logger": "IncentiveHouse ERP", "message": "Server started", "request_id": "abc-123"}
```

### Request ID

Every request gets an `X-Request-ID` header (client-provided or auto-generated). The ID flows into all log entries for that request for traceability.

### SSL / TLS

```bash
# Windows — generate self-signed certs
powershell -ExecutionPolicy Bypass .\scripts\generate_self_signed_cert.ps1

# Linux — generate self-signed certs
bash scripts/generate_self_signed_cert.sh

# Certificates are written to ./certs/
#   ihe-erp.crt  → SSL certificate
#   ihe-erp.key  → SSL private key
```

For production, replace with a trusted CA certificate (Let's Encrypt, ZeroSSL, etc.).

### nginx Reverse Proxy

The included `nginx.conf` provides:
- HTTP → HTTPS redirect
- SSL termination (TLSv1.2 + TLSv1.3)
- Static file caching (30 days, immutable)
- Request ID passthrough
- 100 MB client max body size (for document uploads)

```bash
docker run -d --name ihe-nginx --network ihe-net \
    -v ./nginx.conf:/etc/nginx/nginx.conf:ro \
    -v ./certs:/etc/ssl/certs:ro \
    -p 443:443 -p 80:80 \
    nginx:alpine
```

## Docker Deployment

```bash
# 1. Set SQL_SERVER in .env:
#    - For local Docker SQL Server: SQL_SERVER=sqlserver
#    - For external SQL Server:     SQL_SERVER=<ip-or-hostname>

# 2. Build and run API only (connecting to external SQL Server):
docker compose up -d --build

# 3. Run full local stack (API + SQL Server 2022 Express container):
docker compose --profile local up -d --build

# 4. Run migrations after SQL Server is ready:
docker compose exec api python migrations/01_master_loader.py

# 5. Check logs
docker compose logs -f api

# 6. Stop
docker compose down
```

## Directory Structure (Production)

```
D:\IncentiveHouse_ERP\
├── .env              # Secrets & config (git-ignored)
├── .env.template     # Template for .env
├── app/              # Application code
├── static/           # Static assets (logo, CSS, JS)
├── data/             # Runtime data (neural models, logs)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Backup

Back up these locations regularly:
- `IHE_ERP` SQL Server database
- `D:\IncentiveHouse_ERP\data\` (neural model registry, trained models)
- `D:\Data_Sources\docs\` (source documents for document system)

## Monitoring

- **Health endpoint**: `GET /health` returns `{"status":"healthy","app":"...","version":"..."}`
- **Logs**: Structured JSON-like format via stdlib logging; pipe to systemd journal or Docker logs
- **Uptime**: Use systemd service or Docker `restart: unless-stopped`
