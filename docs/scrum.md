# Scrum Process — citation-builder-scorpio

Managed by **steves-devs** team. See `~/.hermes/skills/devops/steves-devs/SKILL.md` for full roster and process.

## Team

| Role | Agent | Responsibility |
|------|-------|----------------|
| Scrum Master | Scorpio | Process, routing, git |
| Developer | Dev-Scorpio | Code implementation |
| Writer | Doc-Scorpio | Documentation |
| QA | QA-Scorpio | Testing |
| DevOps | Ops-Scorpio | Deployment |

## Statuses

| Status | Meaning |
|--------|---------|
| backlog | Not yet planned |
| sprint | In current sprint, not started |
| in_progress | Dev-Scorpio working |
| review | Scorpio reviewing |
| docs | Doc-Scorpio writing/updating |
| qa | QA-Scorpio testing |
| done | Committed, documented, deployed |

## Sprint cadence

1. **Planning** — pick backlog items, break into tasks, write to `docs/plans/`
2. **Development** — spawn Dev-Scorpio per task, commit each
3. **Documentation** — spawn Doc-Scorpio for new features and at release
4. **QA** — spawn QA-Scorpio after implementation
5. **Review** — Scorpio reviews, merges, pushes
6. **Retro** — write `docs/retro/sprint-<N>.md`

Every change = git commit. Every release = docs updated.

## Sprint 1 Status (May 24–31)

**Goal:** Verify the submission engine works end-to-end, fix bugs from real testing, ship stable v1.0

| ID | Story | Status | Notes |
|----|-------|--------|-------|
| T4 | Add submission progress tracking (live status during batch) | **done** | Implemented polling-based batch progress page with animated bar, stat cards, auto-refreshing table; redirect on batch start updated; committed |
| T3 | Update docs + CHANGELOG for v1.0 release | **in_progress** | Doc-Scorpio updating |
| T2 | Fix bugs found during real testing | **done** | Bugs from T1 fixed and committed |
| T1 | Run real submission test on live app | **done** | Real testing completed |
|| T5 | QA pass — edge cases, error handling | todo | Waiting on docs

## Sprint 2 Status (May 25)

**Goal:** Build analytics dashboard for data-driven insights

| ID | Story | Status | Notes |
|----|-------|--------|-------|
| T6 | Build analytics dashboard route + template | **done** | `GET /analytics` with 7 queries, Chart.js donut/bar charts, tables; deployed to live |
