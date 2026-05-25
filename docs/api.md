# REST API

> All JSON API endpoints for the Local SEO Citation Builder.

## Base URL

All API endpoints are prefixed with the application base URL:

```
https://citation-builder.212.227.153.56.sslip.io
```

Or locally:

```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. CSRF protection is enabled for form-based routes but not enforced on API routes (they use GET requests).

## Endpoints

---

### Dashboard

#### Get Dashboard Stats

```
GET /api/stats
```

Returns aggregate statistics for the dashboard.

**Response 200 (application/json):**

```json
{
  "total_businesses": 12,
  "total_submissions": 284,
  "completed": 168,
  "failed": 42,
  "pending": 58,
  "in_progress": 6,
  "skipped": 10,
  "success_rate": 59.2,
  "captcha_detected": 23
}
```

| Field | Type | Description |
|---|---|---|
| `total_businesses` | integer | Number of businesses in the database |
| `total_submissions` | integer | Total submission records |
| `completed` | integer | Submissions marked completed |
| `failed` | integer | Submissions that failed |
| `pending` | integer | Submissions awaiting processing |
| `in_progress` | integer | Submissions currently being processed |
| `skipped` | integer | Submissions manually skipped |
| `success_rate` | float | Percentage of completed vs total submissions |
| `captcha_detected` | integer | Submissions where CAPTCHA was detected |

---

### Businesses

#### List All Businesses

```
GET /api/businesses
```

Returns all businesses ordered by most recently updated.

**Response 200 (application/json):**

```json
[
  {
    "id": 1,
    "business_name": "Maple Leaf Plumbing",
    "phone": "416-555-0123",
    "address": "123 Yonge Street",
    "city": "Toronto",
    "province": "Ontario",
    "postal_code": "M5V 1A1",
    "website": "https://mapleleafplumbing.ca",
    "email": "info@mapleleafplumbing.ca",
    "description": "Professional plumbing services...",
    "categories": "Plumbing, HVAC, Home Services",
    "created_at": "2026-05-24T10:30:00",
    "updated_at": "2026-05-25T08:15:00",
    "status": "active"
  },
  ...
]
```

#### Get Single Business

```
GET /api/businesses/<id>
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | integer (path) | Business ID |

**Response 200 (application/json):** Single business object (same schema as list item).

**Response 404:** Business not found.

---

### Directories

#### List Directories

```
GET /api/directories
```

Returns directories from the JSON data file, with optional filters.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `province` | string | Filter by province (e.g., `Ontario`) |
| `category` | string | Filter by category (e.g., `general`, `local`) |
| `difficulty` | string | Filter by difficulty level (`easy`, `medium`, `hard`) |
| `search` | string | Search by directory name (case-insensitive) |

**Response 200 (application/json):**

```json
[
  {
    "name": "Yellow Pages Canada",
    "url": "https://www.yellowpages.ca",
    "submission_url": "https://www.yellowpages.ca/business/claim/",
    "category": "general",
    "province_focus": [],
    "difficulty": "medium",
    "requires_captcha": true,
    "field_mapping": {
      "business_name": "businessName",
      "phone": "phoneNumber",
      "address": "streetAddress",
      "city": "addressLocality",
      "province": "addressRegion",
      "postal_code": "postalCode",
      "website": "url",
      "email": "email",
      "description": "description",
      "categories": "category"
    },
    "notes": "Requires account creation..."
  },
  ...
]
```

#### Get Directories by Province

```
GET /api/directories/by_province/<province>
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `province` | string (path) | Province name (e.g., `Ontario`, `British Columbia`) |

**Response 200 (application/json):** Array of directory objects matching the province (including national directories with empty `province_focus`).

---

### Submissions

#### Get Submission Status for a Business

```
GET /api/submissions/<business_id>
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `business_id` | integer (path) | Business ID |

**Response 200 (application/json):**

```json
{
  "business": {
    "id": 1,
    "business_name": "Maple Leaf Plumbing",
    ...
  },
  "stats": {
    "total": 62,
    "completed": 45,
    "failed": 5,
    "pending": 8,
    "in_progress": 2,
    "skipped": 2,
    "captcha": 6,
    "manual": 4,
    "batch_complete": false
  },
  "submissions": [
    {
      "id": 101,
      "business_id": 1,
      "directory_name": "Yellow Pages Canada",
      "directory_url": "https://www.yellowpages.ca",
      "submission_url": "https://www.yellowpages.ca/business/claim/",
      "guide_url": "https://www.yellowpages.ca/business/claim/?business_name=...",
      "screenshot_path": "screenshots/captcha_Yellow_Pages_20260525_120000.png",
      "status": "completed",
      "error_message": null,
      "submitted_at": "2026-05-25T08:15:00",
      "created_at": "2026-05-25T08:14:30",
      "captcha_detected": false
    },
    ...
  ]
}
```

**Stats Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of submission records for this business |
| `completed` | integer | Submissions marked completed |
| `failed` | integer | Submissions that failed |
| `pending` | integer | Submissions awaiting processing |
| `in_progress` | integer | Submissions currently being processed |
| `skipped` | integer | Submissions manually skipped |
| `captcha` | integer | Submissions where CAPTCHA was detected |
| `manual` | integer | Submissions requiring manual action |
| `batch_complete` | boolean | True when all submissions for this business have reached a terminal status (completed/failed/skipped). Used by the batch progress page to know when polling is done. |

#### Start Batch Submission

```
POST /businesses/<id>/start
```

Initiates batch submission for a business to selected (or all) directories. This is a form-based endpoint (not JSON).

**Form Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `directories` | string (optional) | Comma-separated directory names to submit to. If omitted, submits to all directories. |

**Response:** HTTP 302 redirect to the batch progress page (`/businesses/<id>/batch-progress`) with a flash message.

---

### CAPTCHA Queue

#### View CAPTCHA Queue Page

```
GET /captcha-queue
```

Renders an HTML page showing all submissions where CAPTCHA was detected or status is `manual`. This is a form-based route (not JSON API).

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `page` | integer (optional) | Page number for pagination (default: 1, per_page: 25) |

**Response:** HTML page listing submissions with:
- Business name
- Directory name
- Status badge
- Screenshot image (if available)
- Guide link for manual submission
- Retry and Skip action buttons

---

### Submission Actions

#### Retry a Submission

```
POST /submissions/<id>/retry
```

Reset a submission status to `pending` and re-run the submission engine for a single directory.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | integer (path) | Submission ID |

**Response:** HTTP 302 redirect back to the business view page.

#### Skip a Submission

```
POST /submissions/<id>/skip
```

Mark a submission as `skipped` with a manual skip reason.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | integer (path) | Submission ID |

**Response:** HTTP 302 redirect back to the business view page.

---

## Error Responses

### 404 Not Found

```json
{
  "error": "Not Found"
}
```

Returned when a business or submission ID doesn't exist.

### 500 Internal Server Error

Standard Flask 500 error page is returned for unhandled exceptions.

---

## Rate Limiting

There is no rate limiting on the API endpoints. However, the Playwright submission engine has built-in delays (human-like timing) and a 1-second pause between directory submissions during batch processing.

## Notes

- All submission actions (start, retry) run in background threads and update the database asynchronously. The API returns immediately after starting the process.
- Submission status can be polled via `GET /api/submissions/<business_id>` to check progress.
- The CAPTCHA queue is only available as an HTML page; there is no JSON API endpoint for it currently.
