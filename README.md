# 📋 Local SEO Citation Builder

> Automate your Canadian local SEO citation building with a browser-based submission engine.

**Live Demo:** [https://citation-builder.212.227.153.56.sslip.io](https://citation-builder.212.227.153.56.sslip.io)

---

## Features

- **Business Management** — Add, edit, view, and delete business profiles (name, phone, address, website, email, description, categories).
- **70+ Canadian Directories** — Pre-loaded database of Canadian business directories organized by province and category, with field mappings for automation.
- **Playwright Auto-Submission** — Browser automation engine that navigates to directory submission forms and fills them with business data.
- **Human-like Behavior** — Random typing speed (60–160 ms per keystroke), scrolling, and pauses between actions to avoid detection.
- **CAPTCHA Handling** — Auto-detects reCAPTCHA, solves via 2Captcha API, falls back to screenshot + manual review queue.
- **Three Difficulty Levels** — Easy (auto-submit), Medium (auto + CAPTCHA fallback), Hard (guide link for manual submission).
- **Batch Processing** — Submit a business to all directories with one click; runs in background threads.
- **CAPTCHA Queue** — Review and handle unsolved CAPTCHAs with screenshots and guide links.
- **REST API** — JSON endpoints for dashboard stats, business CRUD, directory listing, and submission management.
- **Dark UI** — Clean, modern interface with stats dashboard, badges, pagination, and status indicators.

## Screenshots

> ![Dashboard](https://via.placeholder.com/800x450/1a237e/ffffff?text=Dashboard)
> *Dashboard showing stats overview*
>
> ![Business List](https://via.placeholder.com/800x450/1a237e/ffffff?text=Business+List)
> *Business management interface*
>
> ![Directory List](https://via.placeholder.com/800x450/1a237e/ffffff?text=Directory+List)
> *Directory browser with filter controls*
>
> ![Submission Queue](https://via.placeholder.com/800x450/1a237e/ffffff?text=Submission+Queue)
> *Submission status tracking*
>
> ![CAPTCHA Queue](https://via.placeholder.com/800x450/1a237e/ffffff?text=CAPTCHA+Queue)
> *Manual CAPTCHA review queue*

## Quick Start

### Prerequisites

- Python 3.11+
- Playwright-compatible system (Linux with Chromium dependencies)
- 2Captcha API key (optional, for auto CAPTCHA solving)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/citation-builder.git
cd citation-builder

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Run the application
python run.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `citation-builder-secret-key-change-in-production` | Flask secret key |
| `DATABASE_URL` | `sqlite:///instance/citation.db` | Database connection URI |
| `PLAYWRIGHT_HEADLESS` | `true` | Run Playwright in headless mode |
| `TWOCAPTCHA_API_KEY` | (none) | 2Captcha API key for auto CAPTCHA solving |

### Docker Deployment

```bash
# Build and start
docker compose up -d

# Check logs
docker compose logs -f app

# The app will be available at http://localhost:80
```

See [docs/deployment.md](docs/deployment.md) for full deployment instructions with SSL.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│   nginx     │────▶│   Gunicorn   │
│  (User)     │     │  (proxy +   │     │  (Flask app) │
│             │◀────│   SSL)      │◀────│              │
└─────────────┘     └─────────────┘     └──────┬───────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          │                    │                    │
                    ┌─────▼─────┐      ┌───────▼───────┐    ┌──────▼──────┐
                    │  SQLite   │      │  Playwright   │    │  Directory  │
                    │  Database │      │  (Chromium)   │    │    Data     │
                    │  (DB)     │      │  (Automation) │    │  (JSON)     │
                    └───────────┘      └───────────────┘    └─────────────┘
                                               │
                                        ┌──────▼──────┐
                                        │  2Captcha   │
                                        │  API        │
                                        └─────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Project Structure

```
citation-builder/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── models/
│   │   ├── business.py          # Business SQLAlchemy model
│   │   └── submission.py        # DirectorySubmission model
│   ├── routes/
│   │   ├── dashboard.py         # Dashboard & API stats
│   │   ├── business.py          # Business CRUD & API
│   │   ├── directory.py         # Directory listing & API
│   │   └── submission.py        # Submissions & CAPTCHA queue
│   ├── services/
│   │   └── submission_engine.py # Playwright automation core
│   ├── templates/               # Jinja2 templates (dark theme)
│   ├── static/                  # CSS & JS assets
│   └── data/
│       └── ca_directories.json  # 70+ Canadian directories
├── docs/                        # Documentation
├── nginx/
│   └── default.conf             # nginx config with SSL
├── Dockerfile                   # Production container
├── docker-compose.yml           # Multi-service orchestration
├── requirements.txt             # Python dependencies
├── entrypoint.sh                # Container startup script
├── init_db.py                   # Database initialization
└── run.py                       # Development server
```

## Documentation

| Document | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System architecture, data flow, component diagrams |
| [docs/deployment.md](docs/deployment.md) | Docker deployment, nginx SSL, environment variables |
| [docs/submission-engine.md](docs/submission-engine.md) | Playwright automation, CAPTCHA handling, field mapping |
| [docs/directory-data.md](docs/directory-data.md) | Directory JSON schema, difficulty levels, province targeting |
| [docs/api.md](docs/api.md) | All REST API endpoints |
| [docs/models.md](docs/models.md) | SQLAlchemy models and relationships |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## License

MIT — See LICENSE file for details.
