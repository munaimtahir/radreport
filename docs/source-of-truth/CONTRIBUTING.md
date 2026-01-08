# CONTRIBUTING.md

## Rules
- Do not add features without updating the relevant doc in this pack.
- Keep workflow statuses centralized (single enum source).
- Every new endpoint must have:
  - request/response defined
  - permission defined
  - test added (or smoke test step updated)

## Branching
- `main`: stable, deployable
- `dev`: integration
- feature branches: `feat/<name>`

## Commits
- Use small, descriptive commits
- Include migration files when needed
