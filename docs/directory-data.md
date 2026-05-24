# Directory Data

> Schema, difficulty levels, province targeting, and field mappings for Canadian business directories.

## Overview

The directory database is stored as a single JSON file at `app/data/ca_directories.json`. It contains metadata and an array of directory entries (62+ Canadian business directories) used for citation building.

## File Structure

### Top-Level Schema

```json
{
  "meta": { ... },
  "directories": [ ... ]
}
```

### Meta Object

```json
{
  "meta": {
    "title": "Canadian Business Directories for Citation Building",
    "description": "Comprehensive database of Canadian business directories...",
    "total_entries": 62,
    "last_updated": "2026-05-24",
    "fields_tracked": [
      "business_name", "phone", "address", "city", "province",
      "postal_code", "website", "email", "description", "categories"
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `title` | string | Human-readable title of the data set |
| `description` | string | Summary of what the data contains |
| `total_entries` | integer | Number of directories in the array |
| `last_updated` | string (date) | ISO date of last update |
| `fields_tracked` | array[string] | Business fields this directory supports for mapping |

### Directory Entry Schema

Each entry in the `directories` array:

```json
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
  "notes": "Requires account creation. Phone verification via SMS..."
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Display name of the directory |
| `url` | string | Yes | Main website URL |
| `submission_url` | string | Yes | URL for submitting/claiming a listing |
| `category` | string | Yes | Directory category (see below) |
| `province_focus` | array[string] | No | Provinces this directory targets (empty = national) |
| `difficulty` | string | Yes | Submission difficulty level (`easy`, `medium`, `hard`) |
| `requires_captcha` | boolean | Yes | Whether this directory uses CAPTCHA |
| `field_mapping` | object | Yes | Maps business fields to form field names |
| `notes` | string | No | Human-readable notes for manual submitters |

### Category Values

| Category | Count | Examples |
|---|---|---|
| `general` | ~20 | Yellow Pages, Yelp, Google Business Profile |
| `local` | ~12 | City-specific directories (Toronto.com, VancouversBest) |
| `industry` | ~10 | Industry-specific (Legal, Healthcare, Restaurants) |
| `chamber` | ~5 | Chamber of Commerce listings |
| `government` | ~3 | Government business registries |
| `niche` | ~12 | Niche directories (educational, tourism, events) |

## Difficulty Levels

### Easy

**Auto-submit with Playwright.** Directories where:
- Form fields are straightforward to map
- CAPTCHA is rare or easily solved
- No account creation required (or can be automated)

**Strategy:** Full Playwright automation. Navigate → fill fields → submit.

**Examples:** Canada411, Foursquare, Bing Places, Hotfrog Canada

### Medium

**Try auto-submit, fallback on CAPTCHA.** Directories where:
- Basic form fields exist and can be mapped
- CAPTCHA is common but can often be solved via 2Captcha
- May require account creation or phone verification

**Strategy:** Attempt Playwright auto-submit. If CAPTCHA detected, try 2Captcha. If unsolved, screenshot + manual queue.

**Examples:** Yellow Pages Canada, Yelp Canada, Google Business Profile, Cylex Canada

### Hard

**Immediate guide link, no auto-submit.** Directories where:
- Complex multi-step registration/verification process
- Phone or postcard verification required
- Account creation with login/email verification
- Form is behind authentication

**Strategy:** Return a guide URL with query parameters pre-filled for convenience. No browser automation attempted.

**Examples:** MerchantCircle, some chamber of commerce directories

### Distribution

Based on current data:
- **Easy:** ~18 directories
- **Medium:** ~42 directories
- **Hard:** ~2 directories

## Province Targeting

The `province_focus` field controls which provinces a directory targets:

```json
// National directory (works for all provinces)
{ "province_focus": [] }

// Province-specific directory
{ "province_focus": ["Ontario"] }

// Multi-province directory
{ "province_focus": ["Ontario", "Quebec", "British Columbia"] }
```

### Supported Province Values

| Province | Abbreviation |
|---|---|
| Alberta | AB |
| British Columbia | BC |
| Manitoba | MB |
| New Brunswick | NB |
| Newfoundland and Labrador | NL |
| Northwest Territories | NT |
| Nova Scotia | NS |
| Nunavut | NU |
| Ontario | ON |
| Prince Edward Island | PE |
| Quebec | QC |
| Saskatchewan | SK |
| Yukon | YT |

### Filtering Logic

When filtering by province:

```python
# A directory matches if:
# - province_focus is empty (national), OR
# - the target province is in province_focus
if not d.get('province_focus') or province in d['province_focus']:
    matches.append(d)
```

## Field Mapping System

The `field_mapping` object maps each of the 10 tracked business fields to the directory's form field name. The engine uses this mapping to know which form field to fill for each business attribute.

### Standard Field Map

| Business Field | Type | Example Mapping Value |
|---|---|---|
| `business_name` | string | `"BusinessName"`, `"company"`, `"name"` |
| `phone` | string | `"Phone"`, `"phoneNumber"`, `"telephone"` |
| `address` | string | `"Address"`, `"streetAddress"`, `"street"` |
| `city` | string | `"City"`, `"addressLocality"`, `"town"` |
| `province` | string | `"Province"`, `"state"`, `"region"`, `"StateOrProvince"` |
| `postal_code` | string | `"PostalCode"`, `"zip"`, `"postCode"` |
| `website` | string | `"Website"`, `"url"`, `"WebsiteUrl"` |
| `email` | string | `"Email"`, `"emailAddress"` |
| `description` | text | `"Description"`, `"about"`, `"businessDescription"` |
| `categories` | string | `"Category"`, `"businessCategory"`, `"industry"` |

### Empty Mappings

Some directories don't support all fields. Empty strings indicate unsupported fields:

```json
{
  "field_mapping": {
    "business_name": "businessName",
    "email": "",
    "description": ""
  }
}
```

The engine skips empty mappings during form filling.

## CAPTCHA Requirements

The `requires_captcha` field indicates whether a CAPTCHA challenge is expected:

```json
{ "requires_captcha": true }
```

This flag is informational — the engine always attempts CAPTCHA detection via selectors regardless of this flag. The 2Captcha auto-solve is attempted when:
1. A CAPTCHA is detected via selectors
2. A sitekey can be extracted
3. `TWOCAPTCHA_API_KEY` is configured

## Field Mapping Variations

Different directories use different naming conventions. Common patterns:

| Convention | Examples | Directories |
|---|---|---|
| **camelCase** | `businessName`, `phoneNumber`, `postalCode` | Yellow Pages, Canada411 |
| **PascalCase** | `BusinessName`, `Phone`, `PostalCode` | Bing Places |
| **snake_case** | `business_name`, `phone_number`, `postal_code` | Yelp, Foursquare |
| **lowercase** | `name`, `phone`, `address`, `city` | Google Business Profile |
| **human labels** | `Business Name`, `Phone Number` | Some custom forms |

The field mapping value in the JSON is stored as the directory's form field name. The engine converts this to a CSS selector automatically (trying `#id`, `[name=""]`, `input[name=""]`, etc.).

## Maintenance

### Adding a New Directory

```json
{
  "name": "New Directory Name",
  "url": "https://example.com",
  "submission_url": "https://example.com/add-listing",
  "category": "general",
  "province_focus": ["Ontario"],
  "difficulty": "easy",
  "requires_captcha": false,
  "field_mapping": {
    "business_name": "businessName",
    "phone": "phone",
    "address": "address",
    "city": "city",
    "province": "province",
    "postal_code": "postalCode",
    "website": "website",
    "email": "email",
    "description": "description",
    "categories": "category"
  },
  "notes": "Quick registration form, no verification required."
}
```

### Updating Fields

1. Edit the `ca_directories.json` file
2. Update `meta.total_entries` and `meta.last_updated`
3. Restart the app to pick up changes (the JSON is loaded at runtime on each request)

### Testing Field Mappings

To verify a field mapping works:
1. Navigate to the directory's submission URL in a browser
2. Inspect the form fields to find their `name` attributes
3. Update the `field_mapping` values to match
4. Test with a single-directory submission via the UI
