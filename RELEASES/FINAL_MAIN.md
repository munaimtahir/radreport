# Final Main Release - V2 Locked

**Date:** 2026-02-08
**Status:** V2-only reporting; seeding idempotent; unit tests pass; API smoke pass; E2E not included.

## Canonical Seed Paths
- Block Library: `backend/apps/reporting/seed_data/templates_v2/library/`
- Activation: `backend/apps/reporting/seed_data/templates_v2/activation/`

## Known Deferred Items
- Playwright E2E tests are not included in the "Verify Main" gate (must be run separately).
- Frontend build check is separate.

This marker signifies the official transition to strictly governed V2 reporting.
