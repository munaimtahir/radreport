# E2E Smoke Test Status

## Overview
A Playwright E2E smoke harness has been implemented to verify the V2 reporting workflow.

## Features
- **Deterministic Bootstrap**: Uses API to create patient, visit, and work item before tests.
- **StorageState Auth**: Performs login once and reuses the session.
- **V2 Workflow Coverage**:
  - Login
  - Worklist navigation
  - Report filling (Enums, Numbers, Segmented Booleans)
  - Selective visibility verification
  - Draft saving & persistence check
  - Submission & Verification
  - PDF Preview generation

## Local Execution
```bash
# Setup environment
cp .env.e2e.example .env.e2e
# Edit .env.e2e with target credentials

# Run smoke tests
npm run e2e:smoke
```

## CI/CD
A GitHub Action workflow is configured in `.github/workflows/e2e-smoke.yml`.

## Status
- Harness: **Ready**
- Smoke Spec: **Implemented**
- Bootstrap Strategy: **Implemented (API)**
- Selectors: **Data-testid prioritized**
