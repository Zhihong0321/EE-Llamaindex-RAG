# Security Checklist

## Overview

This document provides a comprehensive security checklist for the LlamaIndex RAG API. Review and complete all items before deploying to production.

**Last Updated**: 2025-01-15  
**Version**: 1.0.0

---

## Pre-Deployment Security Review

### 1. API Key Management ✓

- [x] **OpenAI API Key**
  - [x] Stored in environment variables (not hardcoded)
  - [x] Not committed to version control
  - [x] Not logged in application logs
  - [x] Validated on startup (non-empty check)
  - [ ] Rotated periodically (recommended: every 90 days)
  - [ ] Separate keys for dev/staging/production
  - [ ] Monitored for unusual usage patterns

**Implementation Status**: ✅ Complete
- API key loaded from `OPENAI_API_KEY` environment variable
- Validation in `app/config.py` ensures key is not empty
- Logging configuration excludes sensitive data

**Action Items**:
- [ ] Set up API key rotation schedule
- [ ] Create separate keys for each environment
- [ ] Configure OpenAI usage alerts

---

### 2. Database Security ✓

- [x] **Connection Security**
  - [x] Connection string stored in environment variables
  - [x] Not committed to version control
  - [x] Parameterized queries (SQL injection protection)
  - [ ] SSL/TLS enabled for database connections
  - [ ] Connection string includes `sslmode=require`

- [x] **Access Control**
  - [ ] Dedicated database user (not superuser)
  - [ ] Minimal required privileges granted
  - [ ] Strong password (generated, not manual)
  - [ ] Database access restricted to application IP only

- [x] **Data Protection**
  - [ ] Database backups configured
  - [ ] Backup encryption enabled
  - [ ] Backup retention policy defined
  - [ ] Disaster recovery plan documented

**Implementation Status**: ✅ Partial
- Connection pooling implemented with asyncpg
- Parameterized queries used throughout (SQL injection safe)
- SSL support available via connection string

**Action Items**:
- [ ] Enable SSL: `DB_URL=postgresql://user:pass@host:5432/db?sslmode=require`
- [ ] Create dedicated database user with minimal privileges
- [ ] Configure database backups (daily recommended)
- [ ] Test disaster recovery procedure

**Database User Setup**:
```sql
-- Create dedicated user
CREATE USER rag_api_user WITH PASSWORD 'STRONG_GENERATED_PASSWORD';

-- Grant minimal privileges
GRANT CONNECT ON DATABASE llamaindex_rag TO rag_api_user;
GRANT USAGE ON SCHEMA public TO rag_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rag_api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rag_api_user;

-- Revoke unnecessary privileges
REVOKE CREATE ON SCHEMA public FROM rag_api_user;
```

---

### 3. CORS Configuration ✓

- [x] **Development**
  - [x] Wildcard (`*`) acceptable for local development
  - [x] Configurable via `CORS_ORIGINS` environment variable

- [ ] **Production**
  - [ ] Specific origins only (NO wildcards)
  - [ ] HTTPS origins only
  - [ ] Exact origin matching (including protocol and port)
  - [ ] Documented allowed origins

**Implementation Status**: ✅ Complete
- CORS middleware configured in `app/main.py`
- Supports comma-separated list of origins
- Wildcard support for development

**Action Items**:
- [ ] Set production CORS: `CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com`
- [ ] Verify no wildcard in production
- [ ] Test CORS from allowed origins
- [ ] Document allowed origins in deployment guide

**Example Production Configuration**:
```bash
# Production CORS (specific origins only)
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Development CORS (wildcard acceptable)
CORS_ORIGINS=*
```

---

### 4. Input Validation ✓

- [x] **Request Validation**
  - [x] Pydantic models for all request bodies
  - [x] Field type validation
  - [x] Required field enforcement
  - [x] Custom validators for complex fields

- [x] **Size Limits**
  - [x] Request body size limit (10MB default)
  - [x] Configurable via `MAX_REQUEST_SIZE`
  - [x] Message length validation
  - [x] Document size validation

- [x] **Injection Protection**
  - [x] SQL injection protection (parameterized queries)
  - [x] XSS protection (JSON responses)
  - [x] Command injection protection (no shell execution)

**Implementation Status**: ✅ Complete
- All endpoints use Pydantic models for validation
- FastAPI automatically validates request bodies
- asyncpg uses parameterized queries (SQL injection safe)
- JSON responses prevent XSS

**Validation Examples**:
- `ChatRequest`: Validates `session_id` and `message` are present
- `IngestRequest`: Validates `text` field is present
- `Config`: Validates all environment variables on startup

---

### 5. Authentication & Authorization ⚠️

- [ ] **API Authentication** (Future Enhancement)
  - [ ] API key authentication implemented
  - [ ] JWT token authentication implemented
  - [ ] Rate limiting per API key
  - [ ] API key rotation mechanism

- [ ] **User Authorization** (Future Enhancement)
  - [ ] User-based access control
  - [ ] Session isolation per user
  - [ ] Document access control per user

**Implementation Status**: ⚠️ Not Implemented (MVP Scope)
- Current MVP has no authentication
- All endpoints are publicly accessible
- Sessions are isolated by `session_id` but not authenticated

**Action Items** (Post-MVP):
- [ ] Implement API key authentication
- [ ] Add rate limiting middleware
- [ ] Implement user-based access control
- [ ] Add JWT token support

**Recommended Approach**:
1. Add API key header validation: `X-API-Key`
2. Implement rate limiting: 100 requests/minute per key
3. Add user context to sessions
4. Implement document ownership

---

### 6. Secrets Management ✓

- [x] **Environment Variables**
  - [x] All secrets in environment variables
  - [x] `.env` file in `.gitignore`
  - [x] `.env.example` provided (without secrets)
  - [x] Secrets not logged

- [ ] **Secrets Rotation**
  - [ ] API key rotation schedule defined
  - [ ] Database password rotation schedule defined
  - [ ] Rotation procedure documented

- [ ] **Secrets Storage** (Platform-Specific)
  - [ ] Railway: Secrets stored in Railway dashboard
  - [ ] AWS: Secrets Manager or Parameter Store
  - [ ] GCP: Secret Manager
  - [ ] Azure: Key Vault

**Implementation Status**: ✅ Complete
- All secrets loaded from environment variables
- `.env` file excluded from version control
- Logging configuration excludes sensitive data

**Action Items**:
- [ ] Document secrets rotation procedure
- [ ] Set up secrets rotation schedule (90 days recommended)
- [ ] Use platform-specific secrets management

---

### 7. HTTPS/TLS ✓

- [ ] **Production HTTPS**
  - [ ] HTTPS enabled for all endpoints
  - [ ] Valid SSL/TLS certificate
  - [ ] HTTP redirects to HTTPS
  - [ ] HSTS header enabled

- [ ] **Certificate Management**
  - [ ] Certificate auto-renewal configured
  - [ ] Certificate expiration monitoring
  - [ ] Certificate backup

**Implementation Status**: ⚠️ Platform-Dependent
- Railway provides automatic HTTPS
- Custom deployments require manual HTTPS setup

**Action Items**:
- [ ] Verify HTTPS is enabled in production
- [ ] Test HTTP to HTTPS redirect
- [ ] Configure HSTS header (if not provided by platform)
- [ ] Monitor certificate expiration

**HSTS Header** (if needed):
```python
# Add to app/main.py middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

### 8. Error Handling & Logging ✓

- [x] **Error Handling**
  - [x] Custom exception classes
  - [x] Exception handlers for all error types
  - [x] Appropriate HTTP status codes
  - [x] User-friendly error messages

- [x] **Logging**
  - [x] Structured logging implemented
  - [x] Appropriate log levels
  - [x] No sensitive data in logs
  - [x] Request/response logging

- [ ] **Production Logging**
  - [ ] Log level set to INFO or WARNING
  - [ ] Log aggregation configured
  - [ ] Log retention policy defined
  - [ ] Log monitoring and alerts

**Implementation Status**: ✅ Complete
- Custom exceptions in `app/exceptions.py`
- Exception handlers in `app/main.py`
- Structured logging in `app/logging_config.py`
- Request logging middleware in `app/middleware.py`

**Action Items**:
- [ ] Set production log level: `LOG_LEVEL=INFO` or `WARNING`
- [ ] Configure log aggregation (e.g., Datadog, Sentry)
- [ ] Set up log-based alerts for errors
- [ ] Define log retention policy (30-90 days recommended)

---

### 9. Rate Limiting ⚠️

- [ ] **API Rate Limiting** (Future Enhancement)
  - [ ] Rate limiting middleware implemented
  - [ ] Per-IP rate limiting
  - [ ] Per-API-key rate limiting (when auth added)
  - [ ] Rate limit headers in responses

- [ ] **OpenAI Rate Limiting**
  - [ ] OpenAI rate limits documented
  - [ ] Retry logic with exponential backoff
  - [ ] Rate limit monitoring

**Implementation Status**: ⚠️ Not Implemented (MVP Scope)
- No rate limiting in current implementation
- OpenAI retry logic implemented in `app/retry_utils.py`

**Action Items** (Post-MVP):
- [ ] Implement rate limiting middleware
- [ ] Configure rate limits (e.g., 100 req/min per IP)
- [ ] Add rate limit headers to responses
- [ ] Monitor and adjust rate limits based on usage

**Recommended Implementation**:
```python
# Using slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, ...):
    ...
```

---

### 10. Dependency Security ✓

- [x] **Dependency Management**
  - [x] `requirements.txt` with pinned versions
  - [ ] Regular dependency updates
  - [ ] Security vulnerability scanning

- [ ] **Vulnerability Scanning**
  - [ ] Automated scanning configured (e.g., Dependabot, Snyk)
  - [ ] Regular manual audits
  - [ ] Vulnerability remediation process

**Implementation Status**: ✅ Partial
- Dependencies listed in `requirements.txt`
- Versions not pinned (allows updates)

**Action Items**:
- [ ] Pin dependency versions: `pip freeze > requirements.txt`
- [ ] Enable Dependabot on GitHub
- [ ] Run security audit: `pip-audit` or `safety check`
- [ ] Schedule monthly dependency updates

**Security Audit Commands**:
```bash
# Install pip-audit
pip install pip-audit

# Run security audit
pip-audit

# Or use safety
pip install safety
safety check
```

---

### 11. Container Security ✓

- [x] **Docker Security**
  - [x] Non-root user in container
  - [x] Minimal base image (python:3.11-slim)
  - [x] No unnecessary packages
  - [x] Health check configured

- [ ] **Image Scanning**
  - [ ] Container image vulnerability scanning
  - [ ] Regular base image updates
  - [ ] Image signing (optional)

**Implementation Status**: ✅ Complete
- Dockerfile uses non-root user (`appuser`)
- Minimal base image with only required packages
- Health check configured

**Action Items**:
- [ ] Scan Docker image: `docker scan llamaindex-rag-api:latest`
- [ ] Update base image regularly
- [ ] Consider image signing for production

**Image Scanning**:
```bash
# Using Docker Scout
docker scout cves llamaindex-rag-api:latest

# Using Trivy
trivy image llamaindex-rag-api:latest
```

---

### 12. Network Security ⚠️

- [ ] **Network Isolation**
  - [ ] Database not publicly accessible
  - [ ] API behind firewall/security group
  - [ ] VPC/private network configured

- [ ] **DDoS Protection**
  - [ ] DDoS protection enabled (e.g., Cloudflare)
  - [ ] Rate limiting configured
  - [ ] Traffic monitoring

**Implementation Status**: ⚠️ Platform-Dependent
- Railway provides basic network security
- Custom deployments require manual configuration

**Action Items**:
- [ ] Restrict database access to API IP only
- [ ] Configure firewall rules
- [ ] Enable DDoS protection (Cloudflare recommended)
- [ ] Monitor traffic patterns

---

### 13. Data Privacy ✓

- [x] **Data Handling**
  - [x] No PII logged
  - [x] Session data isolated
  - [x] Message content stored securely

- [ ] **Data Retention**
  - [ ] Data retention policy defined
  - [ ] Old session cleanup implemented
  - [ ] Data deletion mechanism

- [ ] **Compliance** (If Applicable)
  - [ ] GDPR compliance (if EU users)
  - [ ] CCPA compliance (if CA users)
  - [ ] Data processing agreement
  - [ ] Privacy policy published

**Implementation Status**: ✅ Partial
- Session isolation implemented
- No PII in logs
- Data retention not implemented

**Action Items**:
- [ ] Define data retention policy (e.g., 90 days)
- [ ] Implement session cleanup job
- [ ] Add data deletion endpoint (if required)
- [ ] Review compliance requirements

**Session Cleanup Example**:
```sql
-- Delete sessions older than 90 days
DELETE FROM sessions WHERE last_active_at < NOW() - INTERVAL '90 days';

-- Delete orphaned messages
DELETE FROM messages WHERE session_id NOT IN (SELECT id FROM sessions);
```

---

## Security Testing

### Penetration Testing

- [ ] **Automated Testing**
  - [ ] OWASP ZAP scan completed
  - [ ] SQL injection testing
  - [ ] XSS testing
  - [ ] CSRF testing

- [ ] **Manual Testing**
  - [ ] Authentication bypass attempts
  - [ ] Authorization bypass attempts
  - [ ] Input validation testing
  - [ ] Error handling testing

**Action Items**:
- [ ] Run OWASP ZAP scan
- [ ] Perform manual security testing
- [ ] Document findings and remediation
- [ ] Re-test after fixes

### Load Testing

- [ ] **Performance Testing**
  - [ ] Load testing completed
  - [ ] Stress testing completed
  - [ ] DDoS simulation
  - [ ] Resource exhaustion testing

**Action Items**:
- [ ] Run load tests (e.g., with Locust, k6)
- [ ] Test with 100, 1000, 10000 concurrent users
- [ ] Identify bottlenecks
- [ ] Optimize based on results

---

## Incident Response

### Incident Response Plan

- [ ] **Preparation**
  - [ ] Incident response team identified
  - [ ] Contact information documented
  - [ ] Escalation procedures defined
  - [ ] Communication plan established

- [ ] **Detection & Analysis**
  - [ ] Monitoring and alerting configured
  - [ ] Log analysis procedures defined
  - [ ] Incident classification criteria

- [ ] **Containment & Recovery**
  - [ ] Containment procedures documented
  - [ ] Backup and recovery procedures tested
  - [ ] Rollback procedures documented

- [ ] **Post-Incident**
  - [ ] Post-mortem template prepared
  - [ ] Lessons learned process defined
  - [ ] Security improvements tracked

**Action Items**:
- [ ] Create incident response plan
- [ ] Identify incident response team
- [ ] Document procedures
- [ ] Test incident response procedures

---

## Security Contacts

### Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

**Contact**:
- Email: security@yourdomain.com
- PGP Key: [Link to PGP key]
- Response Time: 24-48 hours

**Responsible Disclosure**:
- Report vulnerability privately
- Allow 90 days for remediation
- Coordinate public disclosure

---

## Compliance Checklist

### General Compliance

- [ ] **Documentation**
  - [ ] Security policies documented
  - [ ] Privacy policy published
  - [ ] Terms of service published
  - [ ] Data processing agreement (if applicable)

- [ ] **Auditing**
  - [ ] Security audit completed
  - [ ] Compliance audit completed (if required)
  - [ ] Audit findings remediated
  - [ ] Audit reports archived

### GDPR (If Applicable)

- [ ] Data processing agreement
- [ ] Privacy policy with GDPR requirements
- [ ] Data subject rights implemented (access, deletion, portability)
- [ ] Data breach notification procedures
- [ ] Data protection impact assessment

### CCPA (If Applicable)

- [ ] Privacy policy with CCPA requirements
- [ ] Consumer rights implemented (access, deletion, opt-out)
- [ ] Do Not Sell disclosure
- [ ] Data inventory maintained

---

## Sign-Off

### Pre-Production Sign-Off

**Security Review Completed By**: ___________________  
**Date**: ___________________  
**Signature**: ___________________

**Approved for Production By**: ___________________  
**Date**: ___________________  
**Signature**: ___________________

### Post-Deployment Verification

**Production Deployment Date**: ___________________  
**Security Verification Completed**: ___________________  
**Issues Identified**: ___________________  
**Issues Resolved**: ___________________

---

## Maintenance Schedule

### Regular Security Tasks

**Daily**:
- Monitor error logs for security issues
- Review access logs for suspicious activity

**Weekly**:
- Review security alerts
- Check for dependency vulnerabilities

**Monthly**:
- Security patch updates
- Access control review
- Log analysis

**Quarterly**:
- Security audit
- Penetration testing
- Compliance review
- Incident response drill

**Annually**:
- Comprehensive security assessment
- Third-party security audit
- Disaster recovery testing
- Security training for team

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Next Review Date**: 2025-04-15
