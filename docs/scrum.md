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
