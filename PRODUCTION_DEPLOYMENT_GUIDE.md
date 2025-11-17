# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the LlamaIndex RAG API to production environments, with specific focus on Railway deployment and general cloud platform best practices.

### Current Production Deployment

🚀 **Production URL**: https://eternalgy-rag-llamaindex-production.up.railway.app

- **Platform**: Railway
- **API Docs**: https://eternalgy-rag-llamaindex-production.up.railway.app/docs
- **Health Check**: https://eternalgy-rag-llamaindex-production.up.railway.app/health

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Railway Deployment](#railway-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Security Hardening](#security-hardening)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure you have:

- [ ] **OpenAI API Key**: Valid API key with sufficient credits
- [ ] **Database**: PostgreSQL 12+ with pgvector extension enabled
- [ ] **Environment Variables**: All required variables configured (see below)
- [ ] **CORS Origins**: Specific allowed origins configured (not `*`)
- [ ] **Secrets Management**: API keys stored securely (not in code)
- [ ] **Tests Passing**: All E2E tests pass (`python tests/e2e/run_all_e2e_tests.py`)
- [ ] **Performance Testing**: Load testing completed with acceptable response times
- [ ] **Monitoring**: Health check endpoint accessible
- [ ] **Logging**: Log level set to INFO or WARNING for production
- [ ] **Backup Strategy**: Database backup plan in place

---

## Environment Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...                    # Your OpenAI API key
OPENAI_API_BASE=https://api.openai.com   # Or custom endpoint

# Database Configuration
DB_URL=postgresql://user:pass@host:5432/dbname

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=2                                # 2-4 workers recommended
```

### Optional Environment Variables (with Production Defaults)

```bash
# Model Configuration
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4.1-mini

# Application Behavior
MAX_HISTORY_MESSAGES=10
TOP_K_DEFAULT=5
DEFAULT_TEMPERATURE=0.3

# Security & Performance
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
MAX_REQUEST_SIZE=10485760               # 10MB
REQUEST_TIMEOUT=60                      # 60 seconds

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Environment-Specific Configurations

#### Development
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
WORKERS=1
CORS_ORIGINS=*
```

#### Staging
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
WORKERS=2
CORS_ORIGINS=https://staging.yourdomain.com
```

#### Production
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
WORKERS=4
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## Railway Deployment

Railway provides a simple platform for deploying containerized applications with managed PostgreSQL.

### Step 1: Create Railway Project

1. Go to [Railway](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub repository

### Step 2: Add PostgreSQL Service

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a PostgreSQL instance
4. The `DATABASE_URL` will be automatically injected as `DB_URL`

### Step 3: Enable pgvector Extension

Railway's PostgreSQL doesn't have pgvector by default. You need to enable it:

1. Connect to your Railway PostgreSQL instance:
   ```bash
   railway connect postgres
   ```

2. Enable pgvector:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. Verify installation:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

**Note**: If pgvector is not available, you may need to:
- Use Railway's PostgreSQL template with pgvector pre-installed
- Or deploy your own PostgreSQL container with pgvector

### Step 4: Configure Environment Variables

In Railway project settings, add these variables:

```bash
# Required
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.bltcy.ai  # If using custom endpoint

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=2

# Security
CORS_ORIGINS=https://yourdomain.com

# Optional (override defaults)
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-5-nano-2025-08-07
MAX_HISTORY_MESSAGES=10
TOP_K_DEFAULT=5
```

**Note**: Railway automatically provides `PORT` and `DATABASE_URL` variables.

### Step 5: Configure Build Settings

Railway auto-detects the Dockerfile. Verify these settings:

- **Build Command**: (auto-detected from Dockerfile)
- **Start Command**: (auto-detected from Dockerfile CMD)
- **Health Check Path**: `/health`
- **Health Check Timeout**: 30 seconds

### Step 6: Deploy

1. Push your code to GitHub
2. Railway will automatically build and deploy
3. Monitor deployment logs in Railway dashboard
4. Once deployed, Railway provides a public URL

### Step 7: Run Database Migrations

Migrations run automatically on container startup (see Dockerfile CMD).

To manually run migrations:
```bash
railway run alembic upgrade head
```

### Step 8: Verify Deployment

Test the deployed API:

```bash
# Health check
curl https://your-app.railway.app/health

# Ingest test document
curl -X POST https://your-app.railway.app/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Test document", "title": "Test"}'

# Test chat
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "Hello"}'
```

### Railway-Specific Considerations

**Pricing**:
- Railway charges based on resource usage
- PostgreSQL and API service are billed separately
- Monitor usage in Railway dashboard

**Scaling**:
- Vertical scaling: Increase memory/CPU in service settings
- Horizontal scaling: Increase `WORKERS` environment variable (2-4 recommended)

**Logs**:
- View logs in Railway dashboard
- Logs are structured for easy parsing
- Set `LOG_LEVEL=INFO` or `WARNING` in production

**Custom Domain**:
- Add custom domain in Railway project settings
- Update `CORS_ORIGINS` to include your domain

---

## Docker Deployment

For deploying to other cloud platforms (AWS, GCP, Azure, DigitalOcean, etc.).

### Build Docker Image

```bash
docker build -t llamaindex-rag-api:latest .
```

### Run Locally with Docker Compose

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

### Push to Container Registry

#### Docker Hub
```bash
docker tag llamaindex-rag-api:latest yourusername/llamaindex-rag-api:latest
docker push yourusername/llamaindex-rag-api:latest
```

#### AWS ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag llamaindex-rag-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/llamaindex-rag-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/llamaindex-rag-api:latest
```

#### Google Container Registry
```bash
docker tag llamaindex-rag-api:latest gcr.io/<project-id>/llamaindex-rag-api:latest
docker push gcr.io/<project-id>/llamaindex-rag-api:latest
```

### Deploy to Cloud Platforms

#### AWS ECS/Fargate
1. Create ECS cluster
2. Create task definition with environment variables
3. Create service with load balancer
4. Configure RDS PostgreSQL with pgvector

#### Google Cloud Run
```bash
gcloud run deploy llamaindex-rag-api \
  --image gcr.io/<project-id>/llamaindex-rag-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-...,DB_URL=postgresql://...
```

#### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name llamaindex-rag-api \
  --image yourusername/llamaindex-rag-api:latest \
  --dns-name-label llamaindex-rag-api \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=sk-... DB_URL=postgresql://...
```

---

## Security Hardening

### 1. API Key Management

**DO**:
- ✅ Store API keys in environment variables
- ✅ Use secrets management (Railway Secrets, AWS Secrets Manager, etc.)
- ✅ Rotate API keys periodically
- ✅ Use separate keys for dev/staging/production

**DON'T**:
- ❌ Hardcode API keys in code
- ❌ Commit API keys to version control
- ❌ Log API keys in application logs
- ❌ Share API keys across environments

### 2. Database Security

**Connection Security**:
```bash
# Use SSL for database connections
DB_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```

**Access Control**:
- Create dedicated database user with minimal privileges
- Use strong passwords (generated, not manual)
- Enable connection pooling with limits
- Restrict database access to application IP only

**Example PostgreSQL User Setup**:
```sql
-- Create dedicated user
CREATE USER rag_api_user WITH PASSWORD 'strong_generated_password';

-- Grant minimal required privileges
GRANT CONNECT ON DATABASE llamaindex_rag TO rag_api_user;
GRANT USAGE ON SCHEMA public TO rag_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rag_api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rag_api_user;
```

### 3. CORS Configuration

**Production CORS**:
```bash
# Specific origins only (NO wildcards)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Development CORS**:
```bash
# Wildcard acceptable for local development only
CORS_ORIGINS=*
```

### 4. Input Validation

The application includes built-in validation:
- Request body size limit (10MB default)
- Field validation via Pydantic models
- SQL injection protection via parameterized queries
- XSS protection via JSON responses

### 5. Rate Limiting (Recommended)

Consider adding rate limiting middleware or using a reverse proxy:

**Nginx Example**:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://localhost:8000;
    }
}
```

**Cloudflare**: Use Cloudflare's built-in rate limiting

### 6. HTTPS/TLS

**Always use HTTPS in production**:
- Railway provides automatic HTTPS
- For custom deployments, use Let's Encrypt or cloud provider certificates
- Redirect HTTP to HTTPS

---

## Performance Optimization

### 1. Worker Configuration

**Recommended Workers**:
- Small apps (< 100 req/min): 1-2 workers
- Medium apps (100-1000 req/min): 2-4 workers
- Large apps (> 1000 req/min): 4-8 workers

```bash
WORKERS=2  # Start with 2, scale based on load
```

**Formula**: `workers = (2 × CPU cores) + 1`

### 2. Database Connection Pooling

Current configuration (in `app/db/database.py`):
```python
pool = await asyncpg.create_pool(
    dsn=config.db_url,
    min_size=5,
    max_size=20
)
```

**Tuning**:
- `min_size`: Keep warm connections (5-10)
- `max_size`: Maximum concurrent connections (10-50)
- Formula: `max_size = workers × 10`

### 3. Vector Search Optimization

**Index Type** (in PostgreSQL):
```sql
-- For < 1M vectors: IVFFlat
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For > 1M vectors: HNSW (better performance)
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

**Query Optimization**:
- Tune `top_k` parameter (default: 5)
- Lower `top_k` = faster queries
- Higher `top_k` = better context but slower

### 4. LLM Call Optimization

**Timeouts**:
```python
# In app/services/chat_service.py
llm = OpenAI(
    model=config.chat_model,
    temperature=temperature,
    timeout=30.0,  # 30 second timeout
    max_retries=2   # Retry failed requests
)
```

**Streaming** (Future Enhancement):
- Consider implementing streaming responses for better UX
- Reduces perceived latency

### 5. Caching Strategy (Future)

Consider implementing caching for:
- Frequently accessed documents
- Repeated queries (with TTL)
- Session data (Redis)

### 6. Monitoring Performance

**Key Metrics to Track**:
- Request latency (p50, p95, p99)
- Database query time
- OpenAI API latency
- Error rates
- Memory usage
- CPU usage

---

## Monitoring & Health Checks

### 1. Health Check Endpoint

The API provides a health check at `/health`:

```bash
curl https://your-app.railway.app/health
```

Response:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### 2. Docker Health Check

The Dockerfile includes a built-in health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health').read()"
```

### 3. Application Logs

**Structured Logging**:
All logs are structured with key=value pairs for easy parsing:

```
timestamp=2025-01-15 10:30:45 level=INFO logger=app.main message=Starting up RAG API Server version=0.1.0 environment=production
```

**Log Levels**:
- `DEBUG`: Detailed debugging information (development only)
- `INFO`: General informational messages
- `WARNING`: Warning messages (recommended for production)
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

**Production Recommendation**: `LOG_LEVEL=INFO` or `WARNING`

### 4. Monitoring Tools

**Railway**:
- Built-in metrics dashboard
- CPU, memory, network usage
- Request logs

**External Tools** (Recommended):
- **Sentry**: Error tracking and monitoring
- **Datadog**: Full-stack monitoring
- **New Relic**: Application performance monitoring
- **Prometheus + Grafana**: Custom metrics

### 5. Alerting

Set up alerts for:
- High error rates (> 5%)
- Slow response times (> 5s p95)
- High memory usage (> 80%)
- Database connection failures
- OpenAI API failures

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptoms**:
```
DatabaseConnectionError: Failed to connect to database
```

**Solutions**:
- Verify `DB_URL` is correct
- Check database is running and accessible
- Verify network connectivity
- Check database credentials
- Ensure pgvector extension is installed

**Debug**:
```bash
# Test database connection
psql $DB_URL -c "SELECT version();"

# Check pgvector extension
psql $DB_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### 2. OpenAI API Errors

**Symptoms**:
```
OpenAIServiceError: Failed to communicate with OpenAI API
```

**Solutions**:
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI API status (status.openai.com)
- Verify `OPENAI_API_BASE` if using custom endpoint
- Check API rate limits and quotas
- Ensure sufficient API credits

**Debug**:
```bash
# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 3. Migration Failures

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'head'
```

**Solutions**:
- Ensure Alembic is initialized: `alembic init alembic`
- Check migration files exist in `alembic/versions/`
- Verify database connection
- Run migrations manually: `alembic upgrade head`

#### 4. Memory Issues

**Symptoms**:
- Container OOM (Out of Memory) kills
- Slow performance
- High memory usage

**Solutions**:
- Reduce `WORKERS` count
- Reduce database connection pool size
- Reduce `MAX_HISTORY_MESSAGES`
- Increase container memory allocation
- Monitor memory usage and optimize

#### 5. Slow Response Times

**Symptoms**:
- Chat responses take > 5 seconds
- Timeouts

**Solutions**:
- Reduce `top_k` parameter (fewer documents retrieved)
- Optimize vector index (use HNSW for large datasets)
- Reduce `MAX_HISTORY_MESSAGES`
- Check OpenAI API latency
- Add caching layer

#### 6. CORS Errors

**Symptoms**:
```
Access to fetch at 'https://api.example.com/chat' from origin 'https://app.example.com' has been blocked by CORS policy
```

**Solutions**:
- Add origin to `CORS_ORIGINS`: `CORS_ORIGINS=https://app.example.com`
- Verify origin URL matches exactly (including protocol and port)
- Check for trailing slashes
- Restart application after changing CORS settings

### Debug Mode

Enable debug logging temporarily:

```bash
# Set environment variable
LOG_LEVEL=DEBUG

# Restart application
```

**Warning**: Debug mode logs sensitive information. Use only for troubleshooting and disable in production.

### Getting Help

1. Check application logs first
2. Review this troubleshooting guide
3. Check Railway/platform-specific documentation
4. Review GitHub issues
5. Contact support with:
   - Error messages
   - Relevant logs
   - Environment configuration (redact secrets)
   - Steps to reproduce

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] Health check endpoint returns 200 OK
- [ ] Can ingest documents successfully
- [ ] Can chat and receive responses
- [ ] Sources are returned correctly
- [ ] CORS is configured correctly
- [ ] Logs are being generated
- [ ] Monitoring is active
- [ ] Alerts are configured
- [ ] Database backups are running
- [ ] Performance is acceptable (< 5s response time)
- [ ] Error rate is low (< 1%)
- [ ] Documentation is updated with production URLs

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor error rates and logs
- Check API response times
- Verify OpenAI API usage and costs

**Weekly**:
- Review performance metrics
- Check database size and growth
- Verify backups are successful

**Monthly**:
- Review and rotate API keys
- Update dependencies (security patches)
- Review and optimize costs
- Performance testing

**Quarterly**:
- Security audit
- Disaster recovery testing
- Capacity planning

### Updating the Application

1. Test changes in development/staging
2. Run all tests: `python tests/e2e/run_all_e2e_tests.py`
3. Create backup of production database
4. Deploy to production
5. Monitor logs for errors
6. Verify health check
7. Test critical endpoints
8. Rollback if issues detected

---

## Security Contacts

For security issues:
- **DO NOT** open public GitHub issues
- Email: security@yourdomain.com
- Use responsible disclosure

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [LlamaIndex Documentation](https://docs.llamaindex.ai)
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

**Last Updated**: 2025-01-15
**Version**: 1.0.0
