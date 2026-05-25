# Sprint 1 QA Results

**Date:** May 24, 2026
**Tester:** QA-Scorpio
**Project:** citation-builder-scorpio
**App:** https://citation-builder.212.227.153.56.sslip.io

---

## Summary

| Area | Status |
|------|--------|
| Dashboard | ✅ Pass |
| Business CRUD | ✅ Pass (1 minor) |
| Directory listing | ✅ Pass |
| CAPTCHA queue | ✅ Pass |
| Batch progress page | ✅ Pass (1 major fixed) |
| Submission flow | ✅ Pass (1 minor fixed) |
| Docker / HTTPS | ✅ Pass |

**Bugs found: 6 | Fixed: 2 (B2, B3) | Remaining: 4 minor**

---

## Test Results

### ✅ Dashboard (/)
- Page loads with correct stats (0 submissions, 1 business)
- `/api/stats` returns valid JSON
- All stat cards display correctly

### ✅ Business CRUD
- **Create:** Vancouver Pizza Co created with all 10 fields
- **Edit:** Phone and status updated successfully
- **List:** Both businesses shown with correct data
- **Delete:** Confirmation modal works
- **API:** Both `/api/businesses` and `/api/businesses/<id>` return correct JSON
- ⚠️ Minor: CSRF token lifecycle could cause issues on long-open forms (B1)

### ✅ Directory Listing
- All 70 directories displayed
- Filter by province, category, difficulty all work
- Search by name works
- API returns filtered results correctly

### ✅ CAPTCHA Queue
- Page loads with correct empty state
- Nav link present in base template

### ✅ Batch Progress Page
- Progress bar renders with correct percentages
- Stats cards show completed/total/progress/pending/failed/manual
- Auto-polling at 3-second intervals
- Badges display with correct colors
- "All Done" message on completion
- ✅ Major bug fixed (B2): Tailwind classes replaced with inline styles

### ✅ Submission Submit Page
- All 70 directories shown with checkboxes
- Select All / Deselect All / Select Ready buttons work
- ✅ Minor bug fixed (B3): Button renamed from "Select Pending Only" to "Select Ready"

### ✅ Docker / Deployment
- Both containers running: `citation-builder`, `citation-builder-nginx`
- HTTPS accessible, HTTP redirects to HTTPS
- Healthcheck passes

---

## Bug Log

### Fixed in Sprint 1

| ID | Bug | Severity | Fix |
|----|-----|----------|-----|
| B2 | batch_progress.html used Tailwind classes but Tailwind not loaded | Major | Replaced all Tailwind classes with inline styles |
| B3 | selectPending() function name misleading — selected all non-disabled, not pending only | Minor | Renamed to selectReady() |

### Remaining (Minor)

| ID | Bug | Severity | Notes |
|----|-----|----------|-------|
| B1 | CSRF token may expire on long-open forms | Minor | Add JS to refresh token or warn before expiry |
| B4 | No disabled state on Start Submission button — double-click risk | Minor | Add `disabled` attribute after first click |
| B5 | Error cell shows `-` with grey background for no error | Minor | Cosmetic — low priority |
| B6 | No active nav state highlighting | Minor | Add JS to highlight current page in navbar |

---

## Recommendations
1. **B4 (button disabled state)** — easy win, 5-min fix
2. **B6 (nav active state)** — improves UX significantly, 10-min fix
3. **B1 (CSRF expiry)** — only matters if forms sit open for >1 hour
