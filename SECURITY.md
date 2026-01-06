# Security Guide - RIMS Application

This document outlines security considerations, best practices, and procedures for the RIMS application.

## Security Overview

RIMS handles sensitive patient health information (PHI) and must comply with security standards such as HIPAA (in the US) or similar healthcare data protection regulations in your jurisdiction.

---

## Critical Security Measures

### 1. Authentication & Authorization

#### JWT Token Security
- ✅ JWT tokens expire after 1 hour (access token)
- ✅ Refresh tokens expire after 7 days
- ✅ Tokens are rotated on refresh
- ⚠️ Tokens stored in localStorage (consider httpOnly cookies for enhanced security)

**Recommendations:**
```python
# In settings.py - consider shorter token lifetimes
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Reduce from 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),     # Reduce from 7 days
    "ROTATE_REFRESH_TOKENS": True,
}
```

#### Password Policy
- ✅ Minimum 8 characters required
- ✅ Cannot be similar to username
- ✅ Cannot be common passwords
- ✅ Cannot be entirely numeric

**Enhanced Password Policy (Recommended):**
```python
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,  # Increase from 8
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
```

### 2. Data Protection

#### Encryption at Rest
**Database:**
- Use PostgreSQL with encryption enabled
- Encrypt backup files
- Store credentials securely (environment variables, secrets manager)

**Media Files:**
- PDF reports may contain PHI
- Consider encrypting media directory
- Restrict access to authorized users only

#### Encryption in Transit
- ✅ HTTPS/TLS required for all production traffic
- ✅ Force HTTPS redirect in production settings
- ✅ HSTS headers configured

**Verify SSL Configuration:**
```bash
# Test SSL/TLS configuration
openssl s_client -connect your-domain.com:443 -tls1_2
```

### 3. Input Validation & Sanitization

#### API Input Validation
- ✅ Django REST Framework serializers validate input
- ✅ Field types enforced (CharField, IntegerField, etc.)
- ⚠️ Additional validation needed for file uploads

**File Upload Security (If Implemented):**
```python
# Add to settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.jpg', '.png']

# Validate file type in serializer
def validate_file(self, value):
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError("Unsupported file extension")
    return value
```

#### SQL Injection Prevention
- ✅ Django ORM prevents SQL injection by default
- ⚠️ Never use raw SQL without parameterization

**Safe Raw SQL (If Needed):**
```python
# GOOD - Parameterized
cursor.execute("SELECT * FROM patients WHERE id = %s", [patient_id])

# BAD - Never do this
cursor.execute(f"SELECT * FROM patients WHERE id = {patient_id}")
```

#### XSS Prevention
- ✅ Django auto-escapes template output
- ✅ React escapes JSX by default
- ⚠️ Be careful with `dangerouslySetInnerHTML` in React

### 4. CORS Configuration

Current CORS settings allow specific origins. Update for production:

```python
# Development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Production
CORS_ALLOWED_ORIGINS = [
    "https://your-production-domain.com",
]

# Never use in production:
# CORS_ALLOW_ALL_ORIGINS = True  # ❌ DANGEROUS
```

### 5. Rate Limiting

**Not Currently Implemented - Recommended:**

Add Django rate limiting to prevent abuse:

```bash
pip install django-ratelimit
```

```python
# In views or ViewSets
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='POST')
def api_view(request):
    pass
```

Or use DRF throttling:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### 6. Audit Logging

- ✅ Audit app tracks critical actions
- ✅ Records user, timestamp, action, and object

**Ensure Audit Logging for:**
- Patient record access
- Report creation/modification
- Study status changes
- User authentication events
- Configuration changes

**Review Audit Logs Regularly:**
```bash
# Export audit logs
python manage.py shell
from apps.audit.models import AuditLog
logs = AuditLog.objects.filter(timestamp__gte='2024-01-01')
```

---

## Security Checklist

### Pre-Production

#### Environment Configuration:
- [ ] Strong SECRET_KEY (50+ characters)
- [ ] DEBUG=False in production
- [ ] Strong database password
- [ ] Environment variables not in source control
- [ ] .env file in .gitignore

#### Server Configuration:
- [ ] HTTPS/TLS enabled
- [ ] HSTS headers enabled
- [ ] SSL certificate valid and not expired
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] SSH key-based authentication only
- [ ] Root login disabled

#### Application Security:
- [ ] Password validators enabled
- [ ] CORS configured for production domain only
- [ ] ALLOWED_HOSTS set to production domain
- [ ] Session cookies secure (HTTPS only)
- [ ] CSRF protection enabled
- [ ] Content Security Policy headers
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff

#### Database Security:
- [ ] Database user has minimum required permissions
- [ ] Database not exposed to internet
- [ ] Regular backups configured
- [ ] Backup encryption enabled
- [ ] Connection pooling configured

#### Dependencies:
- [ ] All dependencies up to date
- [ ] Security audit run (pip-audit, npm audit)
- [ ] No known vulnerabilities in dependencies

### Post-Production

#### Monitoring:
- [ ] Error tracking configured (Sentry)
- [ ] Log aggregation setup
- [ ] Uptime monitoring
- [ ] Security event alerts
- [ ] Failed login attempt alerts

#### Maintenance:
- [ ] Regular security updates scheduled
- [ ] Dependency update process
- [ ] Backup restoration tested
- [ ] Incident response plan documented
- [ ] Security audit schedule

---

## Common Security Vulnerabilities & Mitigations

### 1. Broken Authentication

**Risks:**
- Weak passwords
- Session hijacking
- Token theft

**Mitigations:**
- ✅ Strong password policy
- ✅ JWT token expiration
- ✅ Token rotation
- 🔄 Consider: Account lockout after failed attempts
- 🔄 Consider: Multi-factor authentication (MFA)

### 2. Sensitive Data Exposure

**Risks:**
- PHI in logs
- Unencrypted backups
- Debug information in production

**Mitigations:**
- ✅ DEBUG=False in production
- ✅ Environment variables for secrets
- 🔄 Sanitize logs (don't log PHI)
- 🔄 Encrypt backups
- 🔄 Use secrets manager (AWS Secrets Manager, HashiCorp Vault)

### 3. Injection Attacks

**Risks:**
- SQL injection
- XSS
- Command injection

**Mitigations:**
- ✅ Django ORM (prevents SQL injection)
- ✅ Auto-escaping in templates
- ⚠️ Validate all user input
- ⚠️ Sanitize file uploads

### 4. Broken Access Control

**Risks:**
- Unauthorized data access
- Privilege escalation

**Mitigations:**
- ✅ JWT authentication required
- ✅ DRF permission classes
- 🔄 Implement role-based access control (RBAC)
- 🔄 Add object-level permissions
- 🔄 Audit access to sensitive resources

### 5. Security Misconfiguration

**Risks:**
- Default credentials
- Unnecessary services enabled
- Verbose error messages

**Mitigations:**
- ✅ No default credentials in code
- ✅ Minimal service exposure
- 🔄 Regular security reviews
- 🔄 Automated security scanning

---

## Incident Response Plan

### 1. Detection

**Indicators of Compromise:**
- Unusual login patterns
- Unexpected data exports
- High error rates
- Performance degradation
- Failed authentication attempts

**Monitoring Tools:**
- Application logs
- Audit logs
- Server metrics
- Error tracking (Sentry)

### 2. Response

**Immediate Actions:**
1. Isolate affected systems
2. Preserve logs and evidence
3. Assess scope of breach
4. Notify security team
5. Begin investigation

**Communication:**
- Internal notification chain
- Legal/compliance notification
- Customer notification (if required)

### 3. Recovery

1. Patch vulnerability
2. Restore from clean backup (if needed)
3. Reset compromised credentials
4. Review and update security measures
5. Document lessons learned

### 4. Post-Incident

- Conduct post-mortem
- Update security procedures
- Implement additional safeguards
- Train staff on new procedures

---

## Compliance Considerations

### HIPAA (United States)

If deploying in US healthcare settings:

**Required:**
- [ ] Business Associate Agreement (BAA) with hosting provider
- [ ] Encryption at rest and in transit
- [ ] Access controls and audit logs
- [ ] Breach notification procedures
- [ ] Regular security assessments
- [ ] Staff training on PHI handling

**Resources:**
- HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/

### GDPR (European Union)

If handling EU patient data:

**Required:**
- [ ] Data processing agreements
- [ ] Privacy policy
- [ ] User consent management
- [ ] Right to access/deletion
- [ ] Data breach notification (72 hours)
- [ ] Data protection impact assessment (DPIA)

### Other Jurisdictions

Consult local healthcare data protection regulations:
- Canada: PIPEDA
- Australia: Privacy Act 1988
- UK: Data Protection Act 2018
- Others: Consult legal counsel

---

## Security Testing

### Regular Security Assessments

**Monthly:**
```bash
# Dependency audit
cd backend && pip-audit
cd frontend && npm audit

# Check for security updates
pip list --outdated
npm outdated
```

**Quarterly:**
- Penetration testing
- Vulnerability scanning
- Code security review
- Access control audit

**Annually:**
- Full security assessment
- Compliance audit
- Disaster recovery test
- Incident response drill

### Automated Security Scanning

**GitHub Actions (Recommended):**

Create `.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Python Security Scan
        run: |
          pip install pip-audit
          cd backend && pip-audit
      
      - name: Node Security Scan
        run: |
          cd frontend && npm audit
```

---

## Contact

For security issues:
- Email: security@your-organization.com
- Create private security advisory on GitHub

**Do not report security vulnerabilities in public issues.**

---

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/

---

**Last Updated:** January 6, 2026  
**Next Review:** April 6, 2026
