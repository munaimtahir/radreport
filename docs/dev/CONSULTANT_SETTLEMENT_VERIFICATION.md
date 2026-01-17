# Consultant Settlement Verification (MVP)

## Automated checks
- `python manage.py migrate` (completed)
- `python manage.py test apps.consultants.tests` (pass)

## Manual smoke test
Not run in this environment (requires running backend/frontend servers and interactive UI verification).

Planned manual flow:
1) Register visit + choose consultant
2) Add 2 services, pay partial
3) Open settlement page, preview, create draft, finalize
4) Change consultant % rule and confirm finalized settlement totals remain unchanged
