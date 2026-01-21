# MyBudget Deployment Guide

This document provides comprehensive instructions for deploying the MyBudget application in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Bank Feed Configuration (GoCardless)](#bank-feed-configuration-gocardless)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| PostgreSQL | 15+ | Database (if running without Docker) |
| Node.js | 20.0+ | Frontend build and development |
| npm | 10.0+ | Package management |
| Python | 3.11+ | Backend runtime |

### System Requirements

- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Disk**: 1GB free space for application and dependencies
- **Network**: Outbound access for package downloads

---

## Environment Variables

Copy the example environment file and configure for your environment:

```bash
cp backend/.env.example backend/.env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://mybudget:mybudget@localhost:5432/mybudget` |
| `SECRET_KEY` | JWT signing key (generate securely) | `openssl rand -hex 32` |
| `FRONTEND_URL` | Frontend origin for CORS | `http://localhost:5173` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `SESSION_LIFETIME_MINUTES` | `30` | Session token expiry |
| `ENVIRONMENT` | `development` | Environment name (`development`, `staging`, `production`) |
| `DEBUG` | `true` | Enable debug mode (disable in production) |
| `API_V1_PREFIX` | `/api` | API route prefix |

### Security Notes

- **SECRET_KEY**: Generate a secure key for production:
  ```bash
  openssl rand -hex 32
  ```
- **DEBUG**: Always set to `false` in production to prevent sensitive error details from being exposed.
- **DATABASE_URL**: Use strong passwords and consider SSL connections for production databases.

---

## Bank Feed Configuration (GoCardless)

MyBudget supports automatic bank transaction syncing via GoCardless Bank Account Data API (formerly Nordigen). This enables PSD2-compliant Open Banking connections across 2,400+ European banks.

### Getting GoCardless Credentials

1. **Sign up** at [GoCardless Bank Account Data](https://bankaccountdata.gocardless.com/)
2. **Create an application** in the GoCardless dashboard
3. **Copy credentials**: Secret ID and Secret Key

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOCARDLESS_SECRET_ID` | Yes* | Your GoCardless API Secret ID |
| `GOCARDLESS_SECRET_KEY` | Yes* | Your GoCardless API Secret Key |
| `GOCARDLESS_BASE_URL` | No | API base URL (default: `https://bankaccountdata.gocardless.com/api/v2`) |
| `BANK_TOKEN_ENCRYPTION_KEY` | Yes* | Fernet key for encrypting bank tokens |
| `BANK_SYNC_INTERVAL_HOURS` | No | Hours between automatic syncs (default: `6`) |
| `BANK_SYNC_CHECK_INTERVAL_MINUTES` | No | Minutes between sync job checks (default: `5`) |
| `BANK_SYNC_MAX_RETRIES` | No | Max retries for failed syncs (default: `3`) |

*Required only if using GoCardless. Without these, the mock adapter is used for testing.

### Generate Encryption Key

The bank token encryption key must be a valid Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Example Configuration

Add to your `.env` file:

```bash
# GoCardless Bank Account Data API
GOCARDLESS_SECRET_ID=your_secret_id_here
GOCARDLESS_SECRET_KEY=your_secret_key_here
GOCARDLESS_BASE_URL=https://bankaccountdata.gocardless.com/api/v2

# Bank sync settings
BANK_TOKEN_ENCRYPTION_KEY=your_fernet_key_here
BANK_SYNC_INTERVAL_HOURS=6
BANK_SYNC_CHECK_INTERVAL_MINUTES=5
BANK_SYNC_MAX_RETRIES=3
```

### OAuth Callback URL

Configure the OAuth callback URL in your GoCardless dashboard:

- **Development**: `http://localhost:5173/bank-callback`
- **Production**: `https://your-domain.com/bank-callback`

### Supported Countries

GoCardless supports banks in 31 European countries including:
- Belgium (BE), Netherlands (NL), Germany (DE), France (FR)
- United Kingdom (GB), Ireland (IE), Spain (ES), Italy (IT)
- And many more...

Use the `GET /api/institutions?country=BE` endpoint to list available banks by country.

### Mock Adapter (Development)

When GoCardless credentials are not configured, the application automatically uses a mock adapter with test banks:
- Demo Bank (GB)
- Test Bank (NL)
- Sample Credit Union (US)

This allows development and testing without real bank connections.

### Automatic Sync Scheduling

The application runs a background scheduler (APScheduler) that:
1. Checks for due sync jobs every `BANK_SYNC_CHECK_INTERVAL_MINUTES` minutes
2. Syncs active connections every `BANK_SYNC_INTERVAL_HOURS` hours
3. Retries failed syncs with exponential backoff (5min, 15min, 1hr)
4. Marks connections as `NEEDS_ATTENTION` after max retries exceeded

### Connection Health Monitoring

Bank connections have health statuses:
- **HEALTHY**: Active and syncing normally
- **WARNING**: Token expiring within 7 days or sync stale >24 hours
- **ERROR**: Token expired, connection failed, or disconnected

Users receive prompts to re-authenticate expiring connections.

### CSV Import (Fallback)

For banks not supported by GoCardless, users can manually import transactions via CSV:
- `POST /api/import/csv/preview` - Preview import with duplicate detection
- `POST /api/import/csv` - Execute import

Supported formats: comma, semicolon, or tab delimited with configurable column mappings.

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mybudget
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (including dev dependencies)
pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your local settings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn mybudget.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 4. Database Setup (Without Docker)

If running PostgreSQL locally:

```bash
# Create database and user
psql -U postgres
CREATE USER mybudget WITH PASSWORD 'mybudget';
CREATE DATABASE mybudget OWNER mybudget;
\q
```

---

## Production Deployment

### 1. Build Frontend

```bash
cd frontend
npm ci  # Clean install for reproducible builds
npm run build
```

The built files will be in `frontend/dist/`. Serve these files via a static file server or CDN.

### 2. Database Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 3. Run with Gunicorn (Recommended)

For production, use Gunicorn with Uvicorn workers:

```bash
pip install gunicorn

gunicorn mybudget.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

Worker count recommendation: `2 * CPU_CORES + 1`

### 4. Run with Uvicorn

For simpler deployments:

```bash
uvicorn mybudget.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Nginx Reverse Proxy Configuration

Example nginx configuration for production:

```nginx
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend static files
    location / {
        root /var/www/mybudget/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health checks (allow internal access)
    location /health {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Metrics endpoint (restrict to internal networks)
    location /metrics {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        allow 127.0.0.1;
        deny all;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # API Documentation
    location /docs {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### 6. Systemd Service (Optional)

Create `/etc/systemd/system/mybudget.service`:

```ini
[Unit]
Description=MyBudget API Server
After=network.target postgresql.service

[Service]
Type=exec
User=mybudget
Group=mybudget
WorkingDirectory=/opt/mybudget/backend
Environment="PATH=/opt/mybudget/backend/venv/bin"
EnvironmentFile=/opt/mybudget/backend/.env
ExecStart=/opt/mybudget/backend/venv/bin/gunicorn mybudget.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mybudget
sudo systemctl start mybudget
```

---

## Docker Deployment

### 1. Quick Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This starts:
- **postgres**: PostgreSQL 15 database on port 5434
- **backend**: FastAPI application on port 8000
- **frontend**: Vite dev server on port 5173

### 2. Environment Configuration

For Docker deployments, environment variables are configured in `docker-compose.yml`:

```yaml
environment:
  DATABASE_URL: postgresql://mybudget:mybudget@postgres:5432/mybudget
  SECRET_KEY: your-production-secret-key
  ENVIRONMENT: production
  DEBUG: "false"
  FRONTEND_URL: https://your-domain.com
```

For production, create a `docker-compose.prod.yml` override:

```yaml
version: '3.8'

services:
  backend:
    environment:
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      DEBUG: "false"
      FRONTEND_URL: ${FRONTEND_URL}
    command: >
      gunicorn mybudget.main:app
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
    volumes: []  # Remove volume mount for production

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    command: ["nginx", "-g", "daemon off;"]
```

Run with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Persistent Volumes

The `postgres_data` volume persists database data across container restarts:

```yaml
volumes:
  postgres_data:
```

To backup:

```bash
docker run --rm -v mybudget_postgres_data:/data -v $(pwd):/backup alpine \
    tar cvf /backup/postgres_backup.tar /data
```

To restore:

```bash
docker run --rm -v mybudget_postgres_data:/data -v $(pwd):/backup alpine \
    tar xvf /backup/postgres_backup.tar -C /
```

### 4. Building Production Images

Backend:

```bash
cd backend
docker build -t mybudget-backend:latest .
```

For production, the Dockerfile runs migrations and starts Uvicorn:

```dockerfile
CMD alembic upgrade head && uvicorn mybudget.main:app --host 0.0.0.0 --port 8000
```

---

## Health Checks

The application exposes health check endpoints for monitoring and orchestration.

### Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Overall health status | `{"status": "healthy", "timestamp": "...", "version": "1.0.0", "checks": {...}}` |
| `GET /health/ready` | Readiness probe | `{"status": "ready"}` |
| `GET /health/live` | Liveness probe | `{"status": "alive"}` |
| `GET /metrics` | Prometheus metrics | Prometheus text format |

### Health Check Details

**`GET /health`** - Returns comprehensive health status:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000+00:00",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 1.23,
      "error": null
    }
  }
}
```

Status values:
- `healthy`: All components operational
- `degraded`: Some components have issues but service is available

**`GET /health/ready`** - Kubernetes readiness probe:

```json
{"status": "ready"}
```

Returns 200 when the application can serve traffic. Returns error status if database is unavailable.

**`GET /health/live`** - Kubernetes liveness probe:

```json
{"status": "alive"}
```

Returns 200 if the application process is running.

### Kubernetes Probe Configuration

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: mybudget
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 10
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 5
        failureThreshold: 3
```

### Docker Compose Health Check

The PostgreSQL service includes a health check:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U mybudget"]
  interval: 5s
  timeout: 5s
  retries: 5
```

---

## Monitoring

### Prometheus Metrics

The application exposes Prometheus metrics at `GET /metrics`.

#### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `mybudget_inprogress` | Gauge | Currently processing requests |
| `http_requests_created` | Counter | Request creation timestamps |

#### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'mybudget'
    static_configs:
      - targets: ['mybudget-backend:8000']
    metrics_path: /metrics
    scrape_interval: 15s
```

### Structured Logging

The application uses structlog for structured JSON logging in production.

#### Log Format (Production)

```json
{
  "event": "user_login",
  "level": "info",
  "logger": "user_actions",
  "timestamp": "2024-01-15T10:30:00.000000Z",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Log Configuration

- **Development**: Colored console output with `DEBUG=true`
- **Production**: JSON format with `DEBUG=false`

### Logging Best Practices

1. **Centralize logs**: Use a log aggregator (e.g., ELK, Loki, CloudWatch)
2. **Set appropriate levels**: Use INFO in production, DEBUG in development
3. **Monitor error rates**: Alert on increased error log volume
4. **Correlate with metrics**: Use request IDs for tracing

### Alerting Recommendations

Set up alerts for:

| Condition | Threshold | Severity |
|-----------|-----------|----------|
| Error rate | > 1% of requests | Warning |
| Error rate | > 5% of requests | Critical |
| Response time P95 | > 1 second | Warning |
| Response time P99 | > 3 seconds | Critical |
| Health check failures | > 3 consecutive | Critical |
| Database latency | > 100ms | Warning |

### Grafana Dashboard

Import the following metrics for a basic dashboard:

```
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response time P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active requests
mybudget_inprogress
```

---

## Troubleshooting

### Common Issues

**Database connection refused**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres
# or
systemctl status postgresql

# Verify connection string
psql $DATABASE_URL -c "SELECT 1"
```

**Migrations fail**

```bash
# Check current migration state
alembic current

# View migration history
alembic history

# Downgrade if needed
alembic downgrade -1
```

**CORS errors**

Ensure `FRONTEND_URL` matches the exact origin of your frontend (including protocol and port).

**Permission denied on volumes**

```bash
# Fix ownership for Docker volumes
sudo chown -R 1000:1000 ./backend
```

---

## Security Checklist

Before deploying to production:

- [ ] Generate a secure `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Set `DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Use HTTPS with valid SSL certificates
- [ ] Restrict `/metrics` endpoint to internal networks
- [ ] Use strong database passwords
- [ ] Enable PostgreSQL SSL connections
- [ ] Configure rate limiting in nginx/load balancer
- [ ] Review and restrict CORS origins
- [ ] Set up log rotation
- [ ] Configure automated backups

### Bank Feed Security

- [ ] Generate a secure `BANK_TOKEN_ENCRYPTION_KEY` with Fernet
- [ ] Store GoCardless credentials securely (environment variables, not in code)
- [ ] Configure OAuth callback URL in GoCardless dashboard
- [ ] Review bank connection permissions and scopes
- [ ] Monitor for expired/failing connections
- [ ] Implement alerts for sync failures
