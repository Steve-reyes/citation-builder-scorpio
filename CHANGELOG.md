# Changelog

All notable changes to the Local SEO Citation Builder are documented in this file.

## [1.1.0] — 2026-05-25

### Added
- **Real-time Batch Submission Progress Tracking** — New dedicated progress page at `/businesses/<id>/batch-progress` with:
  - Animated progress bar showing overall completion percentage
  - Live stat cards (Total, Completed, In Progress, Pending, Failed, Manual)
  - Auto-polling submissions table that updates in real-time (3-second interval)
  - Color-coded status badges and completion summary
  - Auto-stops polling when batch completes
- **`batch_complete` API Field** — Added to `GET /api/submissions/<business_id>` response; boolean indicating whether all submissions for a business have reached a terminal status (completed/failed/skipped)
- **Redirect on Batch Start** — After starting a batch, users are now redirected to the new progress page instead of back to the business view

### Changed
- Route `POST /businesses/<id>/start` now redirects to `/businesses/<id>/batch-progress` instead of the business detail page
- `app/static/js/app.js` — Added polling logic for the batch progress page

## [1.0.0] — 2026-05-25

### Added
- **Initial Release** — Full-stack Local SEO Citation Builder application.
- **Business Management** — CRUD interface for managing businesses with fields for name, phone, address, city, province, postal code, website, email, description, categories, and status.
- **Directory Database** — 70+ Canadian business directories pre-loaded with field mappings, province targeting, difficulty levels, and CAPTCHA requirements.
- **Playwright Automation Engine** — Browser-based auto-submission to business directories using `playwright` (async API).
- **Human-like Behavior Simulation** — Configurable typing speed (60–160 ms/keystroke), random scrolling, variable pauses (0.3–4.5 s) between actions.
- **CAPTCHA Handling** — Auto-detection via multiple CSS selectors, 2Captcha API integration for reCAPTCHA solving, screenshot fallback for manual review.
- **CAPTCHA Queue** — Dedicated page listing all submissions where CAPTCHAs were detected, with guide links for manual submission.
- **Three Difficulty Levels** — `easy` (full auto-submit), `medium` (auto-submit with CAPTCHA fallback), `hard` (immediate guide link).
- **Field Mapping System** — Maps business profile fields to directory form fields with multi-strategy selector fallback.
- **Dashboard** — Stats overview with success rate, total businesses, submissions by status, and CAPTCHA count.
- **REST API** — JSON endpoints for stats, businesses, directories, submission management, and CAPTCHA queue.
- **Dark SaaS UI** — Clean Tailwind CSS-inspired interface with stats cards, badges, pagination, and status indicators.
- **Background Processing** — Batch submissions run in background threads with database status tracking.
- **Docker Deployment** — Docker Compose with Gunicorn + nginx, health checks, SSL support via Let's Encrypt.
- **SQLite Database** — Lightweight single-file database persisted via Docker volume.
- **Health Check** — Docker health endpoint at `GET /` on port 5000.
- **Entrypoint Script** — Automated database initialization on container start.
