# System Architecture

## Overview

The Local SEO Citation Builder is a Flask web application that automates the submission of business listings to Canadian online directories. It uses Playwright (headless Chromium) to navigate to directory submission forms, fills them with business data using human-like behavior, and handles CAPTCHA challenges automatically or via a manual review queue.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User / Browser                           │
│                     (https://citation-builder.212.227.153.56)   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS (443)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                          nginx (reverse proxy)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • SSL termination (Let's Encrypt)                         │  │
│  │ • Static file serving (/static/, 30d cache)               │  │
│  │ • Proxy to Gunicorn on :5000                              │  │
│  │ • Redirects HTTP → HTTPS                                  │  │
│  │ • Client max body size: 16M                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP (internal, port 5000)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Gunicorn (WSGI Server)                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • 2 workers                                               │  │
│  │ • 120s timeout                                            │  │
│  │ • bind 0.0.0.0:5000                                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Flask Application                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     Blueprints                              │  │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │ dashboard  │ │ business │ │directory │ │ submission │  │  │
│  │  │  (/)       │ │(/business│ │(/direct- │ │(/submiss-  │  │  │
│  │  │  /api/stats│ │  es)     │ │ ories)   │ │ ions, /cap-│  │  │
│  │  └────────────┘ └──────────┘ └──────────┘ │ tcha-queue)│  │  │
│  │                                           └────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     Services                                │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │              SubmissionEngine                         │  │  │
│  │  │  • Playwright async API (Chromium)                   │  │  │
│  │  │  • CAPTCHA detection & solving                        │  │  │
│  │  │  • Human-like behavior simulation                    │  │  │
│  │  │  • Field mapping & form filling                       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────┐  ┌──────────────────────────────┐  │
│  │    SQLAlchemy Models    │  │      Jinja2 Templates         │  │
│  │  ┌─────────────────┐   │  │  • base.html (layout)         │  │
│  │  │ Business         │   │  │  • dashboard/index.html      │  │
│  │  │ DirectorySubmis- │   │  │  • business/*.html (4 pages) │  │
│  │  │ sion             │   │  │  • directory/list.html       │  │
│  │  └─────────────────┘   │  │  • submission/*.html (3 pp)   │  │
│  └─────────────────────────┘  └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
│   SQLite DB     │ │  Directory  │ │  2Captcha    │
│  instance/      │ │  Data JSON  │ │  API (HTTP)  │
│  citation.db    │ │ca_director- │ │              │
│                 │ │ ies.json    │ │              │
└─────────────────┘ └─────────────┘ └──────────────┘
```

## Data Flow

### 1. Business Submission Flow

```
User selects business + directories
         │
         ▼
[POST /businesses/<id>/start]
         │
         ▼
[Create DirectorySubmission records (status=pending)]
         │
         ▼
[Spawn background thread → SubmissionEngine.batch_submit()]
         │
         ├── Pass 1: Hard directories → guide mode (no browser)
         │     └── status = 'manual', guide_url set
         │
         └── Pass 2: Easy + Medium directories → Playwright
               │
               ▼
         [Initialize Chromium browser]
               │
               ▼
         [Navigate to submission_url]
               │
               ▼
         [Wait for page load + human-like delay]
               │
               ▼
         [Random scroll (simulates reading)]
               │
               ▼
         [Detect CAPTCHA?] ──Yes──▶ [Handle CAPTCHA]
               │                          │
              No                    ┌──────┴──────┐
               │                    │              │
               ▼                [Solved?]    [Unsolved?]
         [Fill form fields]         │              │
               │                    │              ▼
               ▼                    │        [Take screenshot]
         [Submit form]              │              │
               │                    │              ▼
               ▼                    │        [status='manual']
         [Check success]◀───────────┘              │
               │                                   │
         ┌─────┴─────┐                             │
         │           │                             │
    [success]   [failed]                           │
         │           │                             │
         ▼           ▼                             │
   [status=    [status=                            │
    completed]  failed]                            │
         │           │                             │
         └───────────┴─────────────────────────────┘
```

### 2. CAPTCHA Queue Flow

```
User visits /captcha-queue
         │
         ▼
[Query: captcha_detected=True OR status='manual']
         │
         ▼
[Display list with screenshots + guide links]
         │
         ▼
[User clicks guide link → manual submission]
         │
         ▼
[User can retry (POST /submissions/<id>/retry)]
         │
         ▼
[Re-runs Playwright for that single directory]
```

## Flask Route → Template Mapping

| Route | HTTP Methods | Blueprint | Template | Description |
|---|---|---|---|---|
| `/` | GET | dashboard | `dashboard/index.html` | Dashboard overview with stats |
| `/api/stats` | GET | dashboard | — (JSON) | Dashboard statistics API |
| `/businesses` | GET | business | `business/list.html` | List all businesses |
| `/businesses/new` | GET, POST | business | `business/create.html` | Create a new business |
|| `/businesses/<id>` | GET | business | `business/view.html` | View business details + Submission History table (Directory, Link, Status, Guide, SS, Error, Submitted, Actions) |
| `/businesses/<id>/edit` | GET, POST | business | `business/edit.html` | Edit a business |
| `/businesses/<id>/delete` | POST | business | — (redirect) | Delete a business |
| `/api/businesses` | GET | business | — (JSON) | List all businesses (API) |
| `/api/businesses/<id>` | GET | business | — (JSON) | Get single business (API) |
| `/directories` | GET | directory | `directory/list.html` | Browse directories with filters |
| `/api/directories` | GET | directory | — (JSON) | List directories (API) |
| `/api/directories/by_province/<p>` | GET | directory | — (JSON) | Directories by province (API) |
| `/submissions` | GET | submission | `submission/list.html` | List all submissions (columns: ID, Directory, Link, Status, Guide, SS, CAPTCHA, Error, Created, Submitted) |
| `/businesses/<id>/submit` | GET | submission | `submission/submit.html` | Submission page for a business |
| `/businesses/<id>/start` | POST | submission | — (redirect) | Start batch submission |
| `/businesses/<id>/batch-progress` | GET | submission | `submission/batch_progress.html` | Real-time batch progress with polling (columns: #, Directory, Link, Status, Error, Submitted) |
| `/submissions/<id>/retry` | POST | submission | — (redirect) | Retry a single submission |
| `/submissions/<id>/skip` | POST | submission | — (redirect) | Skip a submission |
| `/api/submissions/<business_id>` | GET | submission | — (JSON) | Submission status API |
| `/captcha-queue` | GET | submission | `submission/captcha_queue.html` | CAPTCHA manual review queue (columns: ID, Directory, Link, Status, Guide, Screenshot, Business, Created) |
| `/api/submissions/export/<business_id>` | GET | submission | — (CSV) | Export submissions as CSV |

## Component Responsibilities

### Flask Blueprints

- **dashboard** — Home page with aggregate stats (total businesses, submissions by status, success rate, CAPTCHA count). Two routes: HTML view + JSON API.
- **business** — Full CRUD for businesses. Supports pagination, search, and status filtering. Separate API endpoints for programmatic access.
- **directory** — Displays the directory database with client-side filters (province, category, difficulty, search). Computes filter options dynamically from the JSON data.
- **submission** — Manages the submission lifecycle: creating records, starting batch/submission threads, retry/skip actions, and the CAPTCHA queue.

### Services

- **SubmissionEngine** — Core automation class. Handles browser initialization, navigation, CAPTCHA detection/solving, form filling, and submission. Runs Playwright asynchronously, wrapped in synchronous methods for Flask compatibility.

### Data Layer

- **SQLite** — Single-file database (`instance/citation.db`) managed via SQLAlchemy ORM.
- **Directory JSON** — Static data file (`app/data/ca_directories.json`) loaded at runtime, not stored in the database.

## Key Design Decisions

1. **SQLite over PostgreSQL** — Simpler deployment for a single-user/internal tool. Data is small (businesses + submissions), no need for concurrent write scaling.
2. **Background Threads over Celery** — Avoids Redis/celery overhead. Flask's dev server + Gunicorn handle threading fine for this use case. Threads are daemonized (auto-kill on app shutdown).
3. **Async Playwright in Synchronous Context** — The submission engine uses `asyncio.run()` inside a synchronous method. This works smoothly for sequential submissions and avoids converting the entire Flask app to async.
4. **JSON Directory Data, Not DB** — Directories change infrequently and are read-heavy. A JSON file is simpler to edit, version, and deploy than a database table.
5. **Two-Pass Batch Processing** — Hard directories run first (no browser needed, immediate guide links). Easy/Medium directories use the Playwright browser. This minimizes browser startup cost and isolates failures.
