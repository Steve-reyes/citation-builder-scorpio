# Sprint 3 — citation-builder-scorpio

**Duration:** May 25 → June 1
**Goal:** Clean up remaining bugs, add CSV export, ship stable

---

## Backlog Items

| ID | Story | Points | Assignee | Status |
|----|-------|--------|----------|--------|
| T6 | Fix 3 minor bugs — CSRF timeout, button disable, nav active state | 2 | Dev-Scorpio | todo |
| T7 | Export submissions as CSV | 3 | Dev-Scorpio | todo |
| T8 | Docs update + retro | 2 | Doc-Scorpio | todo |

---

## Tasks Breakdown

### T6: Fix remaining bugs
- [ ] B1 — Set WTF_CSRF_TIME_LIMIT to 3600 in config.py
- [ ] B4 — Add onsubmit disable + "Submitting..." text on submit button
- [ ] B6 — Add `active` class to current nav link in base.html
- [ ] Commit

### T7: CSV Export
- [ ] Add "Export CSV" button on submissions page and analytics page
- [ ] New route: GET /api/submissions/<business_id>/export — returns CSV file
- [ ] CSV columns: directory_name, status, captcha_detected, error_message, submitted_at
- [ ] Commit

### T8: Docs
- [ ] CHANGELOG v1.3.0
- [ ] Retro
- [ ] Commit + push

---

## Definition of Done
- [ ] All 3 bugs fixed
- [ ] CSV export working
- [ ] Docs updated
- [ ] Pushed to GitHub
