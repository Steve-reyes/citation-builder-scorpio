# Changelog

All notable changes to the Local SEO Citation Builder are documented in this file.

## [1.4.0] — 2026-05-25

### Added
- **Link Column in All Submission Table Views** — New "Link" column added to four submission table views:
  - **Submission History** (`business/view.html`) — New "Link" column in the existing table
  - **Submissions List** (`submission/list.html`) — Link column added after Directory, shifting Status, Guide, SS, CAPTCHA, Error, and Created/Submitted columns right by one
  - **CAPTCHA Queue** (`submission/captcha_queue.html`) — Link column added after Directory, shifting Status, Guide, Screenshot, Business, and Created columns right by one
  - **Batch Progress** (`submission/batch_progress.html`) — Link column added after Directory in both the static table and the JS-driven dynamic refresh; cell indices shifted by +1 for status (3), error (4), submitted (5)
- **`listing_url` Field** — New database column added to `DirectorySubmission` model (`app/models/submission.py`) that captures the actual listing page URL after successful form submission
- **Post-Submission URL Capture** — Submission engine (`app/services/submission_engine.py`) now captures `page.url` after form submission and returns it as `listing_url` in the result dictionary; only stored when the URL differs from the submission form URL
- **`listing_url` Saved to Database** — `submit_business_to_directory()` persists the captured `listing_url` to the `DirectorySubmission` record on every submission attempt

### Changed
- **Priority-Based Link Display** — All four template tables now use a three-tier link priority system:
  - **📍 `listing_url`** — Shown first with 📍 icon (highest priority — actual live listing page)
  - **🔗 `submission_url`** — Fallback shown with 🔗 icon if no `listing_url` exists
  - **`directory_url`** — Last resort fallback, no icon (directory homepage)
  - URLs truncated to 30-35 characters with ellipsis; full URL shown as `title` tooltip on hover
- **Batch Progress JS** — Dynamic row updates in `batch_progress.html` updated to use the same priority logic: `s.listing_url || s.submission_url || s.directory_url`
- **Database Migration** — `ALTER TABLE directory_submissions ADD COLUMN listing_url VARCHAR(1024)` run on existing database to add the new column

## [1.3.0] — 2026-05-25

### Fixed
- **CSRF Timeout** — `WTF_CSRF_TIME_LIMIT` set to 3600 seconds (1 hour) in `config.py` to prevent form expiry during long submission sessions
- **Submit Button Disable** — Submit button now disables on click with "Submitting..." text to prevent duplicate submissions
- **Nav Active State** — Current navigation link is now highlighted with an `active` CSS class in `base.html` for better UX

### Added
- **CSV Export** — New endpoint `GET /api/submissions/<business_id>/export` returns a downloadable CSV file with columns: `directory_name`, `status`, `captcha_detected`, `error_message`, `submitted_at`. Download button available on the batch progress page.

## [1.2.0] — 2026-05-25

### Added
- **Analytics Dashboard** — New `/analytics` page with:
  - Aggregate stats cards (total businesses, submissions, success rate, CAPTCHA count)
  - Status breakdown donut chart (Chart.js) showing completed/failed/pending/in-progress/skipped proportions
  - Daily trend bar chart for submissions over the last 14 days
  - Difficulty-level performance table with counts and success rates
  - Top 10 and bottom 10 directories ranked by submission count
- **Analytics Nav Link** — "Analytics" entry added to the sidebar navigation in `base.html`
- **Dashboard Route** — `GET /analytics` in `app/routes/dashboard.py` with 7 SQLAlchemy queries

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
