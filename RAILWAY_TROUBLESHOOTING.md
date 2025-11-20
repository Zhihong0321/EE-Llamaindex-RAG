# Railway Deployment Troubleshooting Guide

## Current Status

**Production URL**: https://eternalgy-rag-llamaindex-production.up.railway.app  
**Status**: 🔴 502 Bad Gateway (Application not responding)  
**Last Updated**: 2025-01-15 13:16

## Fixes Applied

### 1. LOG_LEVEL Case Sensitivity ✅
- **Commit**: `003a463`
- **Fix**: Convert LOG_LEVEL to lowercase in Dockerfile
- **Status**: Fixed

### 2. LlamaIndex Circular Import ✅
- **Commit**: `3357c62` → `0e3f784`
- **Fix**: Updated to LlamaIndex v0.10.68 with compatible dependencies
- **Status**: Fixed

### 3. Dependency Conflicts ✅
- **Issue**: Version conflicts between llama-index packages
- **Fix**: Used compatible versions:
  - `llama-index==0.10.68`
  - `llama-index-embeddings-openai==0.1.11`
  - `llama-index-llms-openai==0.1.29`
  - `llama-index-vector-stores-postgres==0.1.14`
- **Status**: Fixed

## Next Steps: Check Railway Dashboard

### 1. View Deployment Logs

Go to your Railway project and check the deployment logs for:

#### Build Phase
Look for:
- ✅ `Successfully installed llama-index-0.10.68`
- ✅ `Successfully installed llama-index-core-0.10.x`
- ❌ Any `ERROR` messages during pip install

#### Runtime Phase
Look for:
- ✅ `INFO  [alembic.runtime.migration] Running upgrade`
- ✅ `INFO:     Started server process`
- ✅ `INFO:     Uvicorn running on http://0.0.0.0:xxxx`
- ❌ Any Python import errors
- ❌ Any database connection errors
- ❌ Any OpenAI API errors

### 2. Common Issues to Check

#### A. Build Still in Progress
- Railway builds can take 3-10 minutes
- Check if "Building..." status is still showing
- Wait for "Deployed" status

#### B. Database Connection Issues
Check if PostgreSQL service is running:
- Go to Railway dashboard → PostgreSQL service
- Verify it's in "Active" state
- Check if pgvector extension is installed

To verify pgvector:
```bash
# In Railway PostgreSQL service, open terminal and run:
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

If not installed:
```bash
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### C. Environment Variables
Verify these are set in Railway:

**Required**:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_API_BASE` - https://api.bltcy.ai (if using custom endpoint)
- `DB_URL` or `DATABASE_URL` - Auto-injected by Railway

**Optional** (with defaults):
- `LOG_LEVEL` - INFO (now case-insensitive)
- `WORKERS` - 2
- `ENVIRONMENT` - production
- `CHAT_MODEL` - gpt-5-nano-2025-08-07
- `EMBEDDING_MODEL` - text-embedding-3-small

#### D. Memory/Resource Limits
- Check if container is running out of memory
- Railway free tier has memory limits
- Consider upgrading if needed

#### E. Port Configuration
- Railway automatically sets `PORT` environment variable
- Dockerfile uses `${PORT:-8000}`
- Verify no port conflicts

### 3. Manual Deployment Check

If build succeeded but app won't start, try these Railway CLI commands:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs in real-time
railway logs

# Check environment variables
railway variables

# Restart the service
railway restart
```

### 4. Test Locally First

Before debugging Railway, verify the app works locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# Test
curl http://localhost:8000/health
```

If it works locally but not on Railway, the issue is environment-specific.

### 5. Rollback Option

If issues persist, you can rollback to a previous deployment:

1. Go to Railway dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Find a working deployment
5. Click "Redeploy"

## Expected Successful Logs

When deployment is successful, you should see:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial schema
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Testing After Successful Deployment

Once the health check returns 200 OK:

```bash
# Quick test
curl https://eternalgy-rag-llamaindex-production.up.railway.app/health

# Full test suite
python test_production.py
```

## Getting Help

If issues persist after checking all above:

1. **Export Railway logs**:
   - Railway dashboard → Service → Logs
   - Copy the full log output
   - Look for the first ERROR message

2. **Check specific error patterns**:
   - `ModuleNotFoundError` → Dependency issue
   - `ConnectionRefusedError` → Database issue
   - `AuthenticationError` → OpenAI API key issue
   - `OperationalError` → Database connection issue

3. **Common Solutions**:
   - Restart the service
   - Rebuild from scratch
   - Check Railway status page (status.railway.app)
   - Verify billing/credits if on free tier

## Contact Information

- Railway Support: https://railway.app/help
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

---

**Last Updated**: 2025-01-15  
**Commits Applied**: `003a463`, `3357c62`, `0e3f784`
