# E2E Smoke Status

- Base URL: `E2E_BASE_URL` (default `http://localhost:8000`; recommended for Docker dev: `http://localhost:5173`)
- Bootstrap method: management command `python manage.py e2e_seed --json-out <path>` (invoked by the smoke test via `E2E_SEED_CMD`)
- Tests added: `e2e/tests/smoke.spec.ts`
- Selectors strategy: `data-testid` only (login, worklist, report actions, and `field-<schemaKey>` for V2 fields)

## Local Run (max 3 commands)
1. `npm install`
2. `docker compose -f docker-compose.dev.yml up -d --build`
3. `E2E_BASE_URL=http://localhost:5173 E2E_API_BASE=http://localhost:8000/api E2E_SEED_CMD="docker compose -f docker-compose.dev.yml exec -T backend python manage.py e2e_seed --json-out /app/e2e_seed.json --username e2e_reporter --password e2e_password" E2E_SEED_JSON=backend/e2e_seed.json npm run e2e:smoke`

## Result
- Status: NOT RUN (no running stack in this environment)
- Known flakes: none
