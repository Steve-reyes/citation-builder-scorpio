# Deployment Guide

## Overview

The Citation Builder is deployed using Docker Compose with three tiers:
1. **Gunicorn** — Flask WSGI server (production Python app server)
2. **nginx** — Reverse proxy with SSL termination
3. **SQLite** — File-based database persisted via Docker volume

## Docker Deployment

### Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- Domain or subdomain pointed to your server's public IP
- Ports 80 and 443 open in your firewall

### Quick Deploy

```bash
# Clone the repository
git clone https://github.com/your-org/citation-builder.git
cd citation-builder

# Set environment variables
export SECRET_KEY="your-strong-secret-here"
export TWOCAPTCHA_API_KEY="your-2captcha-key"  # optional

# Set up SSL certificates (see SSL section below)

# Build and start services
docker compose up -d --build

# Verify health
docker compose ps
curl -f http://localhost:5000/  # Should return HTML

# Follow logs
docker compose logs -f app
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | `citation-builder-secret-key-change-in-production` | Flask session signing key. **Must change in production.** |
| `DATABASE_URL` | No | `sqlite:////app/instance/citation.db` | Database URI. Override for external databases. |
| `PLAYWRIGHT_HEADLESS` | No | `true` | Run Chromium in headless mode (`true`/`false`). |
| `TWOCAPTCHA_API_KEY` | No | (empty) | 2Captcha API key for automatic reCAPTCHA solving. |
| `FLASK_ENV` | No | `production` | Flask environment mode. |

Set environment variables via `.env` file (recommended):

```bash
# .env
SECRET_KEY=your-strong-secret-here
TWOCAPTCHA_API_KEY=your-2captcha-key
```

Or pass them directly:

```bash
SECRET_KEY="..." TWOCAPTCHA_API_KEY="..." docker compose up -d
```

### Docker Compose Services

**app** (Gunicorn + Flask):

```yaml
app:
  build: .
  container_name: citation-builder
  ports:
    - "5000:5000"
  environment:
    - FLASK_ENV=production
    - SECRET_KEY=${SECRET_KEY:-change-this-to-random-secret}
    - DATABASE_URL=sqlite:////app/instance/citation.db
    - TWOCAPTCHA_API_KEY=${TWOCAPTCHA_API_KEY:-}
  volumes:
    - ./instance:/app/instance
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 15s
```

**nginx** (reverse proxy + SSL):

```yaml
nginx:
  image: nginx:alpine
  container_name: citation-builder-nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
    - ./www/certbot:/var/www/certbot:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  depends_on:
    - app
  restart: unless-stopped
```

### Dockerfile

The production container:

1. Starts from `python:3.11-slim`
2. Installs Chromium system dependencies (libnss3, libcups2, libgbm1, etc.)
3. Installs Python dependencies from `requirements.txt`
4. Installs Playwright's Chromium browser
5. Copies the application code
6. Initializes the database schema via `init_db.py`
7. Starts via `entrypoint.sh` which runs Gunicorn with 2 workers

## nginx SSL Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install certbot
apt-get install certbot

# Obtain certificate for your domain
certbot certonly --webroot -w ./www/certbot \
  -d citation-builder.yourdomain.com

# Copy certificates to nginx SSL directory
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/citation-builder.yourdomain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/citation-builder.yourdomain.com/privkey.pem nginx/ssl/key.pem

# Restart nginx
docker compose restart nginx
```

### Option 2: Self-Signed (Development)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/CN=citation-builder.local"
```

### Auto-Renewal (Let's Encrypt)

Add a cron job to renew certificates:

```bash
# crontab -e
0 3 * * * certbot renew --quiet && docker compose restart nginx
```

### nginx Configuration

Key aspects of `nginx/default.conf`:

- **Port 80** — Redirects all HTTP traffic to HTTPS via `301`
- **Port 443** — SSL termination with TLSv1.2/TLSv1.3, strong cipher suites
- **Static files** — Served directly by nginx from `/app/static/` with 30-day cache (`public, immutable`)
- **Proxy** — All other requests forwarded to `http://app:5000` with proper headers (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`)
- **Client max body** — 16 MB (for form submissions)

## Health Checks

### Docker Health Check

The `app` service has a built-in health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

The check curls the dashboard homepage. A successful HTTP response (status 200) indicates the app is healthy.

### Manual Health Check

```bash
# Via Docker
docker inspect --format='{{json .State.Health}}' citation-builder

# Via HTTP directly to the app
curl -f http://localhost:5000/

# Via nginx
curl -f https://citation-builder.212.227.153.56.sslip.io/
```

### Health Check Response

The dashboard route (`GET /`) returns an HTML page. A successful response means:
- Flask is running and serving templates
- SQLAlchemy can query the database (stats are computed on each request)
- The app is accessible via the full stack

## Database

### Persistence

The SQLite database is stored in `./instance/citation.db` and mounted as a Docker volume:

```yaml
volumes:
  - ./instance:/app/instance
```

### Backup

```bash
# Backup the database
cp ./instance/citation.db ./backups/citation-$(date +%Y%m%d_%H%M%S).db

# Restore a backup
cp ./backups/citation-20260525_120000.db ./instance/citation.db
docker compose restart app
```

### Migration

The app uses `db.create_all()` on startup, which creates tables if they don't exist. For schema changes:

1. Stop the app: `docker compose stop app`
2. Backup the database
3. Update the models
4. Run a migration script (the app will add new columns/ tables on restart, but won't alter existing ones)
5. Restart: `docker compose up -d`

## Scaling Considerations

- **Workers** — Gunicorn is configured with 2 workers. Increase for higher concurrency: edit `entrypoint.sh` to add `--workers 4`.
- **Playwright** — Each submission uses a single Chromium instance. Multiple concurrent batch submissions share the browser. For heavy concurrent use, consider a queue-based architecture with Celery.
- **SQLite** — Suitable for single-user/small-team use. For multi-user concurrent access, migrate to PostgreSQL by changing `DATABASE_URL`.

## Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `502 Bad Gateway` | Gunicorn not started | Check logs: `docker compose logs app` |
| `SSL: error:02001002` | Missing certificate files | Run SSL setup or generate self-signed certs |
| Playwright timeout | Directory URL unreachable or slow | Check directory URL in JSON, increase timeout |
| `CAPTCHA not solved` | No 2Captcha key or wrong sitekey | Verify `TWOCAPTCHA_API_KEY`, check sitekey extraction |
| Database locked | Multiple concurrent write attempts | Reduce worker count, switch to PostgreSQL |
| `Permission denied` | Container can't write to volume | Check `instance/` directory permissions: `chmod 755 instance/` |
