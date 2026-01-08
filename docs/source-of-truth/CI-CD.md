# CI-CD.md

## CI (GitHub Actions suggested)
- Lint backend
- Run unit tests
- Build frontend (if applicable)
- Optional: docker build

## CD (VPS)
- Pull latest code
- Run migrations
- Collect static/build frontend
- Restart services
- Reload Caddy

## Deployment Safety
- Always run smoke tests after deploy:
  - reception create + receipt
  - USG draft→verify→publish
  - OPD vitals→finalize→publish
