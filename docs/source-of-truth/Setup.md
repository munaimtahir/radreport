# Setup.md

## Local (Recommended)
1. Copy `.env.example` → `.env`
2. Start docker:
   - `docker compose up -d --build`
3. Run migrations:
   - `docker compose exec backend python manage.py migrate`
4. Create admin user
5. Seed Service Catalog (CSV import)
6. Open UI and run smoke tests in Tests.md

## VPS (Production)
- Use Caddy reverse proxy
- Backend binds to 127.0.0.1
- Run migrations on deploy
- Keep backups for DB and uploaded documents
