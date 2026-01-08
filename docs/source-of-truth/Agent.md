# Agent.md

## Roles
- **Cursor (Architect + Refactorer):** Lock structure, refactor code, ensure consistency.
- **Codex (Runner + Tester):** Build Docker, run migrations, seed data, execute smoke tests.
- **Human (Product Owner):** Approves workflows, service catalog, templates, and UI theme.

## Guardrails (Non‑Negotiable)
1. **No new features** until workflows are stable end-to-end.
2. Delete unused screens, routes, models, and dead code.
3. One source of truth for:
   - status enums
   - ID formats
   - roles & permissions
4. Never break printing/PDF requirements.
5. Store service **price snapshot** at billing time.
6. Every state transition must be logged (audit trail).
7. If something is unclear, pick the safest option:
   - data integrity > UI convenience > performance

## Tools & Workflow Order (Locked)
1. Cursor: design/lock models, APIs, UI pages, permissions, workflows.
2. Codex: run Docker, migrations, seeds, smoke tests.
3. If systemic issues: create a structured fix prompt + apply in Cursor.
4. Only move forward after all smoke tests pass.
