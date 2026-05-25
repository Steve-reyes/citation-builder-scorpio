# Sprint Retrospective — Sprint 1

**Project:** citation-builder-scorpio
**Date:** May 25, 2026
**Duration:** May 24 — May 25 (2 days)

---

## What went well
- Batch progress tracking built and deployed in single sprint
- Doc subagent workflow worked — docs updated automatically after every feature
- QA caught 6 bugs, 2 fixed same day
- Team of subagents (Dev, Doc, QA) coordinated without conflicts
- All commits pushed, app stayed live throughout

## What sucked
- T1 (real submission test) skipped — no 2Captcha key available, couldn't validate engine end-to-end
- QA ran out of tool calls before it could commit its own findings and fixes — Scorpio had to handle the tail
- Some minor bugs left unfixed (4 cosmetic/minor items)

## What to improve next sprint
- Get 2Captcha API key configured so we can actually test submissions
- Set higher tool limits for QA subagent or split QA into smaller tasks
- Close out minor bugs before calling sprint done

## Action items
- [ ] Get 2Captcha key from Boss and configure it
- [ ] Fix remaining 4 minor bugs (B1, B4, B5, B6)
