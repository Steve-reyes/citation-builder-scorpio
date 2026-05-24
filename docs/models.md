# Data Models

> SQLAlchemy models for the Local SEO Citation Builder.

## Overview

The application uses SQLAlchemy ORM with SQLite as the database backend. Two models are defined:

1. **Business** — Represents a local business with its contact and profile information
2. **DirectorySubmission** — Tracks the submission status for each business-to-directory pair

## Entity Relationship Diagram

```
┌───────────────────────┐          ┌──────────────────────────────┐
│       Business        │          │    DirectorySubmission       │
├───────────────────────┤          ├──────────────────────────────┤
│ id (PK)               │◀──────┼──│ id (PK)                     │
│ business_name         │          │ business_id (FK)            │
│ phone                 │          │ directory_name              │
│ address               │          │ directory_url               │
│ city                  │          │ submission_url              │
│ province              │          │ guide_url                   │
│ postal_code           │          │ screenshot_path             │
│ website               │          │ status                      │
│ email                 │          │ error_message               │
│ description           │          │ submitted_at                │
│ categories            │          │ created_at                  │
│ created_at            │          │ captcha_detected            │
│ updated_at            │          │                              │
│ status                │          │                              │
└───────────────────────┘          └──────────────────────────────┘
```

**Relationship:** A Business has many DirectorySubmission records. When a Business is deleted, all related submissions are cascade-deleted.

---

## Business Model

**Table:** `businesses`

**File:** `app/models/business.py`

### Schema

| Column | Type | Constraints | Default | Description |
|---|---|---|---|---|
| `id` | `Integer` | Primary Key, Auto-increment | — | Unique identifier |
| `business_name` | `String(255)` | NOT NULL | — | Business name |
| `phone` | `String(50)` | Nullable | `None` | Phone number |
| `address` | `String(255)` | Nullable | `None` | Street address |
| `city` | `String(100)` | Nullable | `None` | City |
| `province` | `String(100)` | Nullable | `None` | Province/territory |
| `postal_code` | `String(20)` | Nullable | `None` | Postal code |
| `website` | `String(500)` | Nullable | `None` | Website URL |
| `email` | `String(255)` | Nullable | `None` | Email address |
| `description` | `Text` | Nullable | `None` | Business description |
| `categories` | `String(500)` | Nullable | `None` | Comma-separated categories |
| `created_at` | `DateTime` | Default: `utcnow` | Current UTC time | Record creation timestamp |
| `updated_at` | `DateTime` | Default: `utcnow`, On Update: `utcnow` | Current UTC time | Last update timestamp |
| `status` | `String(20)` | Default: `'draft'` | `'draft'` | Business status (draft, active, paused) |

### SQLAlchemy Definition

```python
class Business(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    website = db.Column(db.String(500))
    email = db.Column(db.String(255))
    description = db.Column(db.Text)
    categories = db.Column(db.String(500),
        comment='Comma-separated categories')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
        default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='draft',
        comment='draft, active, paused')

    submissions = db.relationship(
        'DirectorySubmission',
        backref='business',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
```

### Relationships

| Attribute | Type | Description |
|---|---|---|
| `submissions` | `Query` (dynamic) | All DirectorySubmission records for this business. Supports `.filter()`, `.count()`, `.all()` etc. Cascade delete: removing a Business removes all its submissions. |

### Methods

#### `to_dict()`

Converts the model to a JSON-serializable dictionary:

```python
def to_dict(self):
    return {
        'id': self.id,
        'business_name': self.business_name,
        'phone': self.phone,
        'address': self.address,
        'city': self.city,
        'province': self.province,
        'postal_code': self.postal_code,
        'website': self.website,
        'email': self.email,
        'description': self.description,
        'categories': self.categories,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        'status': self.status,
    }
```

#### `__repr__()`

```python
def __repr__(self):
    return f'<Business {self.id}: {self.business_name}>'
```

### Status Values

| Value | Meaning |
|---|---|
| `draft` | Business created but not yet submitted to directories |
| `active` | Business actively being submitted to directories |
| `paused` | Submissions temporarily paused for this business |

---

## DirectorySubmission Model

**Table:** `directory_submissions`

**File:** `app/models/submission.py`

### Schema

| Column | Type | Constraints | Default | Description |
|---|---|---|---|---|
| `id` | `Integer` | Primary Key, Auto-increment | — | Unique identifier |
| `business_id` | `Integer` | Foreign Key (`businesses.id`), NOT NULL | — | Associated business |
| `directory_name` | `String(255)` | NOT NULL | — | Directory display name |
| `directory_url` | `String(500)` | Nullable | `None` | Directory homepage URL |
| `submission_url` | `String(500)` | Nullable | `None` | URL for submitting a listing |
| `guide_url` | `String(1024)` | Nullable | `None` | Pre-filled guide link for manual submission |
| `screenshot_path` | `String(500)` | Nullable | `None` | Path to CAPTCHA screenshot image |
| `status` | `String(20)` | Default: `'pending'` | `'pending'` | Submission status |
| `error_message` | `Text` | Nullable | `None` | Error details if failed |
| `submitted_at` | `DateTime` | Nullable | `None` | Timestamp of submission attempt |
| `created_at` | `DateTime` | Default: `utcnow` | Current UTC time | Record creation timestamp |
| `captcha_detected` | `Boolean` | Default: `False` | `False` | Whether CAPTCHA was detected |

### SQLAlchemy Definition

```python
class DirectorySubmission(db.Model):
    __tablename__ = 'directory_submissions'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer,
        db.ForeignKey('businesses.id'), nullable=False)
    directory_name = db.Column(db.String(255), nullable=False)
    directory_url = db.Column(db.String(500))
    submission_url = db.Column(db.String(500))
    guide_url = db.Column(db.String(1024))
    screenshot_path = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.String(20),
        default='pending',
        comment='pending, in_progress, completed, failed, skipped, manual'
    )
    error_message = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    captcha_detected = db.Column(db.Boolean, default=False)
```

### Relationships

| Attribute | Type | Description |
|---|---|---|
| `business` | `Business` (backref) | The associated Business object. Accessible as `submission.business`. |

### Methods

#### `to_dict()`

Converts the model to a JSON-serializable dictionary:

```python
def to_dict(self):
    return {
        'id': self.id,
        'business_id': self.business_id,
        'directory_name': self.directory_name,
        'directory_url': self.directory_url,
        'submission_url': self.submission_url,
        'guide_url': self.guide_url,
        'screenshot_path': self.screenshot_path,
        'status': self.status,
        'error_message': self.error_message,
        'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'captcha_detected': self.captcha_detected,
    }
```

#### `__repr__()`

```python
def __repr__(self):
    return f'<DirectorySubmission {self.id}: {self.directory_name} ({self.status})>'
```

### Status Values

| Value | Meaning | Description |
|---|---|---|
| `pending` | Awaiting processing | Submission created but not yet attempted |
| `in_progress` | Currently being processed | Playwright browser is actively working on this submission |
| `completed` | Successfully submitted | Form was filled and submitted successfully |
| `failed` | Submission failed | An error occurred during automation |
| `skipped` | Manually skipped | User chose to skip this directory |
| `manual` | Manual submission needed | CAPTCHA unsolved or hard difficulty — guide link provided |

### Status Lifecycle

```
pending ──→ in_progress ──→ completed
                              ↕
                            failed ◄── retry ── pending
                              ↕
                            skipped
                              ↕
                            manual ◄── captcha_detected
```

---

## Common Queries

```python
# All businesses with active status
Business.query.filter_by(status='active').all()

# Count completed submissions for a business
Business.query.get(1).submissions.filter_by(status='completed').count()

# All submissions where CAPTCHA was detected
DirectorySubmission.query.filter_by(captcha_detected=True).all()

# Submissions needing manual review (CAPTCHA or manual status)
from sqlalchemy import or_
DirectorySubmission.query.filter(
    or_(
        DirectorySubmission.captcha_detected == True,
        DirectorySubmission.status == 'manual',
    )
).all()

# Recent submissions ordered by creation time
DirectorySubmission.query.order_by(
    DirectorySubmission.created_at.desc()
).limit(20).all()

# Success rate calculation
total = DirectorySubmission.query.count()
completed = DirectorySubmission.query.filter_by(status='completed').count()
success_rate = round((completed / total * 100), 1) if total > 0 else 0
```

## Database Initialization

The database is initialized in the Flask app factory:

```python
with app.app_context():
    db.create_all()
```

This creates all tables if they don't exist. The `init_db.py` script also calls this and prints table statistics.

The database file is stored at:
- **Development:** `<project_root>/instance/citation.db`
- **Docker:** `/app/instance/citation.db` (mounted as a volume)
