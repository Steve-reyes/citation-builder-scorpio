# Submission Engine

> How the Playwright automation engine works — CAPTCHA handling, human-like behavior, and field mapping.

## Overview

The `SubmissionEngine` class (in `app/services/submission_engine.py`) is the core automation component. It uses Playwright's async API to control a headless Chromium browser, navigating to business directory submission forms and filling them with business data.

## Architecture

```
SubmissionEngine
├── __init__(headless)        — Initialize with headless mode
├── submit_to_directory()     — Main async submission method
├── submit_business_to_directory() — Sync wrapper (updates DB)
├── batch_submit()            — Submit to multiple directories
│
├── Browser Management
│   └── _init_browser()       — Launch Chromium with args
│
├── Human Simulation
│   ├── _human_delay()        — Random delay between actions
│   ├── _random_scroll()      — Simulate reading the page
│   └── Human timing constants (6 ranges)
│
├── Form Filling
│   ├── _fill_form_fields()   — Map business data to form fields
│   ├── _submit_form()        — Find and click submit button
│   └── Multi-strategy selectors
│
├── CAPTCHA Handling
│   ├── _detect_captcha()     — Check for captcha indicators
│   ├── _extract_sitekey()    — Get reCAPTCHA sitekey
│   ├── _solve_via_2captcha() — Call 2Captcha API
│   ├── _inject_captcha_token() — Inject solved token
│   ├── _take_screenshot()    — Full-page screenshot fallback
│   └── _handle_captcha()     — Orchestrate solve or fallback
│
└── Success Detection
    └── Success indicators (9 keywords checked in page text)
```

## Difficulty Levels

The engine processes directories in two passes based on difficulty:

| Level | Strategy | Browser Required |
|---|---|---|
| **Easy** | Full auto-submit via Playwright. Navigate, fill fields, submit. | Yes |
| **Medium** | Try auto-submit. If CAPTCHA detected, try 2Captcha auto-solve. If unsolved, mark as manual with guide link and screenshot. | Yes |
| **Hard** | Skip auto-submit entirely. Immediately return a guide link with pre-filled query parameters for manual submission. | No |

### Two-Pass Batch Processing

```python
# Pass 1: Hard → immediate guide mode (no browser)
guide_dirs = [d for d in directories if d.get('difficulty') == 'hard']
for directory in guide_dirs:
    result = self.submit_business_to_directory(business, directory)

# Pass 2: Easy + Medium → Playwright attempt
auto_dirs = [d for d in directories if d.get('difficulty') != 'hard']
for directory in auto_dirs:
    result = self.submit_business_to_directory(business, directory)
```

## Human-Like Behavior Simulation

The engine uses carefully calibrated timing to mimic human browsing patterns:

### Timing Constants

| Constant | Range | When Used |
|---|---|---|
| `HUMAN_TYPING_SPEED` | 60–160 ms | Between keystrokes when typing into fields |
| `HUMAN_SHORT_PAUSE` | 0.3–0.9 s | After clicking, before the next action |
| `HUMAN_MEDIUM_PAUSE` | 1.0–2.5 s | After page loads, before interacting |
| `HUMAN_LONG_PAUSE` | 2.5–4.5 s | Between major actions (reading time) |
| `HUMAN_SCROLL_PAUSE` | 0.4–1.2 s | Between scroll events |
| `HUMAN_CLICK_DELAY` | 0.1–0.4 s | Before clicking on elements |
| `HUMAN_FIELD_PAUSE` | 0.2–0.8 s | Between filling form fields |

### Random Scrolling

Before filling a form, the engine simulates reading the page:

```python
async def _random_scroll(page):
    scrolls = random.randint(1, 3)    # 1-3 scroll actions
    for _ in range(scrolls):
        delta = random.randint(200, 700)  # 200-700px each
        await page.evaluate(f'window.scrollBy(0, {delta})')
        await self._human_delay(*HUMAN_SCROLL_PAUSE)
    await page.evaluate('window.scrollTo(0, 0)')  # Scroll back to form
    await self._human_delay(0.5, 1.0)
```

### Typing Simulation

Instead of using `page.fill()` (which sets the value instantly), the engine uses `page.type()` with per-character delays:

```python
await el.click()                                    # Click field
await el.fill('')                                   # Clear existing content
await self._human_delay(0.1, 0.3)                   # Brief pause
await el.type(str(value), delay=random.randint(
    60, 160                                         # 60-160ms per keystroke
))
```

For `<select>` elements, it uses `select_option()` since select menus have discrete options.

## CAPTCHA Handling

The engine implements a multi-layered CAPTCHA strategy.

### 1. CAPTCHA Detection

Uses 10 CSS selectors to detect CAPTCHA presence:

```python
CAPTCHA_INDICATORS = [
    'iframe[src*="recaptcha"]',          # reCAPTCHA iframe
    'iframe[src*="captcha"]',            # Generic captcha iframe
    'div.g-recaptcha',                   # reCAPTCHA widget
    'div.recaptcha',                     # Alternate class
    '#captcha',                          # ID-based
    '.captcha',                          # Class-based
    'input[name*="captcha"]',            # Input field
    'iframe[title*="captcha"]',          # Accessible iframe
    'iframe[title*="recaptcha"]',        # Accessible reCAPTCHA
    '[data-sitekey]',                    # Any element with sitekey
]
```

Detection runs twice:
1. **Before form filling** — On page load, before interacting
2. **After form filling** — Some directories load CAPTCHA after form interaction

### 2. Sitekey Extraction

Two methods to extract the reCAPTCHA sitekey:

```python
# Method 1: data-sitekey attribute
sitekey = page.evaluate('''
    () => {
        const el = document.querySelector('[data-sitekey]');
        return el ? el.getAttribute('data-sitekey') : null;
    }
''')

# Method 2: Parse from iframe src URL
sitekey = page.evaluate('''
    () => {
        const iframe = document.querySelector('iframe[src*="recaptcha"]');
        if (!iframe) return null;
        const match = iframe.src.match(/[?&]k=([^&]+)/);
        return match ? match[1] : null;
    }
''')
```

### 3. 2Captcha Auto-Solving

When a sitekey is extracted and `TWOCAPTCHA_API_KEY` is configured:

```python
# Step 1: Submit CAPTCHA to 2Captcha
POST https://2captcha.com/in.php
    key=API_KEY
    method=userrecaptcha
    googlekey=SITEKEY
    pageurl=PAGE_URL
    json=1
→ Response: {"status": 1, "request": "CAPTCHA_ID"}

# Step 2: Poll for result (up to 150 seconds, polling every 5s)
GET https://2captcha.com/res.php
    key=API_KEY
    action=get
    id=CAPTCHA_ID
    json=1
→ Response: {"status": 1, "request": "SOLVED_TOKEN"}
     OR: {"status": 0, "request": "CAPCHA_NOT_READY"}
```

### 4. Token Injection

After receiving the solved token from 2Captcha, the engine injects it into the page:

```python
page.evaluate('''
    () => {
        // Set the textarea value
        const ta = document.getElementById('g-recaptcha-response');
        if (ta) { ta.innerHTML = TOKEN; ta.value = TOKEN; }

        // Trigger callback if reCAPTCHA loaded
        if (typeof ___grecaptcha_cfg !== 'undefined') {
            for (const c of Object.values(___grecaptcha_cfg.clients)) {
                for (const widget of Object.values(c || {})) {
                    if (widget && widget.callback) widget.callback(TOKEN);
                }
            }
        }

        // Fire events to notify the page
        if (ta) {
            ta.dispatchEvent(new Event('change', { bubbles: true }));
            ta.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
''')
```

### 5. Screenshot Fallback

If 2Captcha fails or isn't configured, the engine takes a full-page screenshot:

```python
# Save to: app/static/screenshots/captcha_DIRECTORY_NAME_TIMESTAMP.png
await page.screenshot(path=filepath, full_page=True)
```

The screenshot path is stored in the `DirectorySubmission.screenshot_path` field and displayed in the CAPTCHA queue page for manual review.

## Field Mapping System

### Mapping Structure

Each directory in `ca_directories.json` has a `field_mapping` object that maps business model fields to form field names:

```json
{
  "field_mapping": {
    "business_name": "BusinessName",
    "phone": "Phone",
    "address": "Address",
    "city": "City",
    "province": "StateOrProvince",
    "postal_code": "PostalCode",
    "website": "WebsiteUrl",
    "email": "Email",
    "description": "Description",
    "categories": "Category"
  }
}
```

Each key is a `Business` model attribute. Each value is the form field name from the target directory.

### Multi-Strategy Selector Resolution

For each mapped field, the engine tries multiple CSS selectors in order:

```python
selectors = [
    f'#{form_field}',                                      # By ID
    f'input[name="{form_field}"]',                         # By name (input)
    f'textarea[name="{form_field}"]',                      # By name (textarea)
    f'select[name="{form_field}"]',                        # By name (select)
    f'[name="{form_field}"]',                              # By attribute
    f'input[placeholder*="{form_field}"]',                 # By placeholder
    f'label:has-text("{form_field}") + input',             # Label-sibling (input)
    f'label:has-text("{form_field}") + textarea',          # Label-sibling (textarea)
    f'label:has-text("{form_field}") + select',            # Label-sibling (select)
]
```

The engine stops at the first matching selector, clicks the element, then fills it appropriately (type for text inputs, `select_option` for dropdowns).

### Empty Mappings

Some directories don't support all fields. Empty strings in field_mapping indicate unsupported fields:

```json
{
  "field_mapping": {
    "email": "",
    "description": ""
  }
}
```

These are skipped during form filling.

## Submit Button Detection

The engine uses 28 submit button selectors in priority order:

| Category | Examples |
|---|---|
| Type-based | `button[type="submit"]`, `input[type="submit"]` |
| Text-based | `button:has-text("Submit")`, `button:has-text("Register")` |
| Link-based | `a:has-text("Submit")`, `a:has-text("Add Listing")` |
| Class-based | `[class*="submit"]`, `[class*="btn-primary"]` |
| ARIA-based | `[aria-label*="submit" i]`, `[aria-label*="register" i]` |
| Positional | `form button:last-of-type`, `form input[type="image"]` |

### Fallback Chain

1. Try each of the 28 selectors
2. If none match, press `Enter` key
3. If that fails, click the last button/input in any form element

## Submission Success Detection

After submitting, the engine checks for success indicators in the page body text:

```python
success_indicators = [
    'thank you', 'submitted', 'success', 'confirmation',
    'listing created', 'your listing', 'claim submitted',
]
```

If any indicator is found, the submission is marked `completed`. Otherwise, it's still marked `completed` with a warning note (the form likely worked but the confirmation text wasn't recognized).

## Error Handling

| Scenario | Behavior |
|---|---|
| Navigation timeout (>30s) | Returns error, status = `failed` |
| Directory URL unreachable | Returns error, status = `failed` |
| No submit button found | Returns error, status = `failed` |
| CAPTCHA unsolved | Takes screenshot, status = `manual`, guide_url set |
| 2Captcha API down | Falls back to screenshot + manual |
| Unexpected exception | Caught at sync wrapper level, status = `failed` |
| Empty field mapping | Skips form filling entirely (likely guide-only) |

## Database Updates

The synchronous wrapper `submit_business_to_directory()` handles all database operations:

```python
# Find or create submission record
submission = DirectorySubmission.query.filter_by(
    business_id=business.id,
    directory_name=directory['name'],
).first()

if not submission:
    submission = DirectorySubmission(
        business_id=business.id,
        directory_name=directory['name'],
        ...
    )

# Update based on result
submission.captcha_detected = result.get('captcha_detected', False)
submission.guide_url = result.get('guide_url')
submission.screenshot_path = result.get('screenshot_path', '')

if result.get('success'):
    submission.status = 'completed'
elif result.get('guide_url'):
    submission.status = 'manual'
else:
    submission.status = 'failed'
    submission.error_message = result.get('error_message')
```

## Batch Progress Tracking

When batch submission is initiated, the user is redirected to a real-time progress page at `/businesses/<id>/batch-progress` that polls the API every 3 seconds for live updates.

### Flow

```
POST /businesses/<id>/start   →   batch_progress() route renders template
                                         ↓
                              Progress page polls GET /api/submissions/<id>
                                         ↓
                              UI updates: progress bar, stat cards, table rows
                                         ↓
                              When batch_complete=true → polling stops
                                         ↓
                              "All done!" message with summary + link back
```

### Page Components (batch_progress.html)

| Component | Description |
|-----------|-------------|
| **Status Badge** | Shows "Running…" or "✓ All Done" based on `stats.batch_complete` |
| **Progress Bar** | Animated gradient bar: `(completed + failed + skipped) / total × 100%` |
| **Stat Cards** | Six live cards: Total, Completed (green), In Progress (blue), Pending (orange), Failed (red), Manual (purple) |
| **Submission Table** | Lists all directories with status badges, error messages, and submission timestamps; cells update in-place on each poll |
| **Done Message** | Green summary card shown on completion with success/fail/manual counts and a link back to the business view |

### `batch_complete` Heuristic

The `batch_complete` field is computed both in the template route and the API endpoint:

```python
# In batch_progress() route (template rendering):
'batch_complete': total > 0 and done == total

# In api_submission_status() (JSON API):
'batch_complete': len(submissions) > 0 and all(
    s.status in ('completed', 'failed', 'skipped')
    for s in submissions
)
```

A submission is considered "terminal" if its status is `completed`, `failed`, or `skipped`. The in_progress and pending statuses mean the batch is still running.

### Polling Logic

The JavaScript in `app/static/js/app.js` handles client-side polling:

- **Interval**: 3,000 ms (3 seconds)
- **Endpoint**: `GET /api/submissions/<business_id>` (returns JSON)
- **On update**: Re-renders progress bar width, stat card values, status badges, error messages, and timestamps for each row
- **On completion**: When `stats.batch_complete` transitions to `true`, polling is stopped via `clearInterval()`, the badge flips to "All Done", and the summary card appears
- **Stale data**: If the page is loaded after the batch is already complete, polling is never started (initial JS check of `batchComplete`)
