# Production Deployment Checklist

Use this checklist to ensure a smooth production deployment of RIMS.

## Pre-Deployment

### Environment Setup
- [ ] Server meets minimum requirements (2GB RAM, 2 CPU cores, 20GB disk)
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] Caddy installed and running
- [ ] Domain DNS configured to point to server
- [ ] Firewall configured (ports 80, 443, 22 open)

### Configuration
- [ ] Repository cloned to `/opt/apps/rims` (or your preferred location)
- [ ] `.env.prod` created from `.env.prod.example`
- [ ] `DJANGO_SECRET_KEY` generated (50+ random characters)
- [ ] `DB_PASSWORD` set to strong password
- [ ] `DJANGO_ALLOWED_HOSTS` configured with your domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` configured with your domain(s)
- [ ] Run `bash scripts/validate-deployment.sh` - all checks pass

## Deployment

### Build and Start
- [ ] Build images: `docker compose --env-file .env.prod build`
- [ ] Start services: `docker compose --env-file .env.prod up -d`
- [ ] Check service status: `docker compose ps` - all services "Up"
- [ ] Check logs for errors: `docker compose logs -f`

### Database Setup
- [ ] Migrations completed (automatic via entrypoint.sh)
- [ ] Create superuser: `docker compose exec backend python manage.py createsuperuser`
- [ ] Verify database connection from backend

### Static Files
- [ ] Static files collected (automatic via entrypoint.sh)
- [ ] Verify static files accessible: `ls -la backend/staticfiles/`

### Caddy Configuration
- [ ] Caddyfile updated with RIMS block (see CADDYFILE_SNIPPET.md)
- [ ] Caddy configuration validated: `caddy validate --config /etc/caddy/Caddyfile`
- [ ] Caddy reloaded: `sudo systemctl reload caddy`
- [ ] SSL certificate obtained successfully

## Verification

### Backend Health
- [ ] Backend health check passes: `curl http://127.0.0.1:8015/api/health/`
  - Expected: `{"status":"ok"}`
- [ ] Backend responds via Caddy: `curl https://yourdomain.com/api/health/`
- [ ] Django admin accessible: `https://yourdomain.com/admin/`
- [ ] Can login with superuser credentials
- [ ] API docs accessible: `https://yourdomain.com/api/docs/`

### Frontend Health
- [ ] Frontend responds locally: `curl http://127.0.0.1:8081/`
- [ ] Frontend loads via browser: `https://yourdomain.com/`
- [ ] No console errors in browser
- [ ] All assets load correctly
- [ ] Navigation works

### API Functionality
- [ ] Can obtain JWT token via `/api/auth/token/`
- [ ] Can access protected endpoints with token
- [ ] CORS working correctly for frontend

### File Serving
- [ ] Static files load (CSS, JS)
- [ ] Media file upload works
- [ ] Media file download works

## Post-Deployment

### Monitoring Setup
- [ ] Log rotation configured
- [ ] Disk space monitoring enabled
- [ ] Service restart policies verified
- [ ] Health checks working

### Backup Strategy
- [ ] Database backup tested: `docker compose exec db pg_dump -U rims rims > backup.sql`
- [ ] Backup restore tested
- [ ] Media files backup strategy in place
- [ ] Automated backup schedule configured

### Documentation
- [ ] Team trained on deployment procedures
- [ ] Emergency contact information documented
- [ ] Rollback procedure tested
- [ ] Incident response plan in place

### Security Hardening
- [ ] `.env.prod` file permissions restricted (600)
- [ ] Firewall rules reviewed
- [ ] SSH key authentication enabled
- [ ] Unnecessary services disabled
- [ ] Security updates applied
- [ ] Monitoring alerts configured

## Testing Checklist

### Functional Testing
- [ ] User registration/login works
- [ ] Patient management works
- [ ] Study creation works
- [ ] Report generation works
- [ ] PDF generation works
- [ ] All CRUD operations work

### Performance Testing
- [ ] Page load times acceptable
- [ ] API response times acceptable
- [ ] Database query performance acceptable
- [ ] Static file serving fast

### Stress Testing
- [ ] Multiple concurrent users tested
- [ ] Large file uploads tested
- [ ] System stable under load

## Maintenance

### Regular Tasks
- [ ] Weekly: Review logs for errors
- [ ] Weekly: Check disk space
- [ ] Weekly: Verify backups
- [ ] Monthly: Update Docker images
- [ ] Monthly: Update system packages
- [ ] Quarterly: Security audit
- [ ] Quarterly: Performance review

### Update Procedure
- [ ] Pull latest code: `git pull origin main`
- [ ] Review changelog
- [ ] Test in staging (if available)
- [ ] Create backup
- [ ] Build new images: `docker compose build`
- [ ] Stop services: `docker compose down`
- [ ] Start services: `docker compose up -d`
- [ ] Verify deployment
- [ ] Monitor for issues

## Rollback Procedure

If deployment fails:
- [ ] Stop services: `docker compose down`
- [ ] Checkout previous version: `git checkout <previous-commit>`
- [ ] Restore database if needed
- [ ] Rebuild and restart: `docker compose up -d --build`
- [ ] Verify rollback successful
- [ ] Document what went wrong

## Emergency Contacts

- **System Admin**: _________________
- **Developer**: _________________
- **Database Admin**: _________________
- **On-Call**: _________________

## Notes

Document any deployment-specific notes, issues encountered, or deviations from standard procedure:

```
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
```

---

## Quick Reference Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart backend

# Execute management commands
docker compose exec backend python manage.py <command>

# Database backup
docker compose exec db pg_dump -U rims rims > backup_$(date +%Y%m%d).sql

# Database restore
cat backup.sql | docker compose exec -T db psql -U rims rims

# Check service health
curl http://127.0.0.1:8015/api/health/
curl http://127.0.0.1:8081/

# Reload Caddy
sudo systemctl reload caddy

# Update deployment
git pull && docker compose up -d --build
```

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Version/Commit**: _______________  
**Status**: ⬜ Success ⬜ Failed ⬜ Partial  
