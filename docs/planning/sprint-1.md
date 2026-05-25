# Sprint 1 — citation-builder-scorpio

**Duration:** May 24 — May 31
**Goal:** Verify the submission engine works end-to-end, fix bugs from real testing, ship stable v1.0

---

## Backlog Items

| ID | Story | Points | Assignee | Status |
|----|-------|--------|----------|--------|
| T1 | Run real submission test on live app | 3 | Dev-Scorpio | todo |
| T2 | Fix bugs found during real testing | 5 | Dev-Scorpio | todo |
| T3 | Update docs + CHANGELOG for v1.0 release | 2 | Doc-Scorpio | todo |
| T4 | Add submission progress tracking (live status during batch) | 3 | Dev-Scorpio | todo |
| T5 | QA pass — edge cases, error handling | 3 | QA-Scorpio | todo |

---

## Tasks Breakdown

### T1: Real submission test

- [ ] Set 2Captcha API key in `.env`
- [ ] Trigger batch submit for "Toronto SEO Agency" (Business ID 1)
- [ ] Monitor submissions: track completed vs failed vs captcha
- [ ] Log all errors and unexpected behavior
- [ ] Commit findings to `docs/testing/sprint-1-results.md`

### T2: Bug fixes

- [ ] Fix any navigation/timeout issues from T1
- [ ] Fix field mapping mismatches
- [ ] Fix CAPTCHA detection false positives
- [ ] Improve error messages
- [ ] Commit each fix individually

### T3: Documentation

- [ ] Update docs with any new findings from T1
- [ ] Add testing guide
- [ ] Update CHANGELOG with v1.0.1
- [ ] Commit

### T4: Live submission progress

- [ ] Add WebSocket or polling-based live status on submission page
- [ ] Show real-time completed/total counter during batch
- [ ] Auto-refresh submission list during active batches
- [ ] Commit

### T5: QA pass

- [ ] Test business CRUD (create, edit, delete)
- [ ] Test directory filtering (province, category, difficulty)
- [ ] Test captcha queue page
- [ ] Test edge cases (empty fields, special chars, long descriptions)
- [ ] Document any bugs found
- [ ] Commit

---

## Definition of Done
- [ ] All code committed with clear messages
- [ ] Real submission test completed with documented results
- [ ] Docs updated
- [ ] CHANGELOG updated
- [ ] Pushed to GitHub
