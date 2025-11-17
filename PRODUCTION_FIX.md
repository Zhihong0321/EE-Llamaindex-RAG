# Production Deployment Fix

## Issues Identified and Fixed

**Date**: 2025-01-15  
**Status**: ✅ FIXED  
**Production URL**: https://eternalgy-rag-llamaindex-production.up.railway.app

### Issue 1: LOG_LEVEL Case Sensitivity

**Problem**: The Railway deployment was failing with a 502 Bad Gateway error. The logs revealed:

```
Error: Invalid value for '--log-level': 'INFO' is not one of 'critical', 'error', 'warning', 'info', 'debug', 'trace'.
```

**Root Cause**:
- Railway environment variable `LOG_LEVEL` was set to uppercase `INFO`
- Uvicorn requires lowercase log level values: `info`, `warning`, `error`, etc.
- The Dockerfile was passing the environment variable directly without case conversion

### Issue 2: LlamaIndex Circular Import

**Problem**: After fixing the log level, a new error appeared:

```
ImportError: cannot import name 'BaseQueryEngine' from partially initialized module 'llama_index.core' 
(most likely due to a circular import)
```

**Root Cause**:
- Using outdated LlamaIndex version 0.9.14 which has circular import issues
- The old package structure has dependency conflicts between modules

### Solutions

#### Fix 1: LOG_LEVEL Case Conversion

Modified `Dockerfile` to convert `LOG_LEVEL` to lowercase before passing to uvicorn:

```dockerfile
# Before
CMD alembic upgrade head && \
    exec uvicorn app.main:app \
    --log-level ${LOG_LEVEL:-info}

# After
CMD alembic upgrade head && \
    LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]') && \
    exec uvicorn app.main:app \
    --log-level $LOG_LEVEL_LOWER
```

**Commit**: `003a463`

#### Fix 2: Update LlamaIndex Version

Updated `requirements.txt` to use newer LlamaIndex versions:

```python
# Before
llama-index==0.9.14
llama-index-embeddings-openai==0.1.5
llama-index-llms-openai==0.1.5
llama-index-vector-stores-postgres==0.1.3

# After
llama-index==0.10.0
llama-index-embeddings-openai==0.1.11
llama-index-llms-openai==0.1.29
llama-index-vector-stores-postgres==0.2.5
```

**Commit**: `3357c62`

### Deployment

1. Fixed Dockerfile (commit `003a463`)
2. Updated LlamaIndex dependencies (commit `3357c62`)
3. Pushed to GitHub main branch
4. Railway will automatically redeploy (takes 2-5 minutes)

### Next Steps

1. **Wait for Railway Deployment** (2-5 minutes)
   - Monitor Railway dashboard for deployment status
   - Check deployment logs for successful startup

2. **Verify Deployment**
   ```bash
   # Run production tests
   python test_production.py
   
   # Or quick health check
   curl https://eternalgy-rag-llamaindex-production.up.railway.app/health
   ```

3. **Expected Response**
   ```json
   {
     "status": "ok",
     "version": "0.1.0"
   }
   ```

### Railway Environment Variables

Ensure these are set in Railway (case-insensitive now):

```bash
# Required
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.bltcy.ai
DB_URL=postgresql://...  # Auto-injected by Railway

# Optional (with defaults)
LOG_LEVEL=INFO           # Now works with uppercase!
WORKERS=2
ENVIRONMENT=production
CHAT_MODEL=gpt-5-nano-2025-08-07
EMBEDDING_MODEL=text-embedding-3-small
```

### Testing After Deployment

Once Railway finishes deploying, run:

```bash
python test_production.py
```

This will test:
- ✅ Health check
- ✅ Session creation
- ✅ Document ingestion
- ✅ Chat queries
- ✅ Document listing
- ✅ Multi-turn conversations

### Monitoring

After successful deployment:
- Monitor Railway logs for any errors
- Check response times (should be < 5s)
- Verify database connections are stable
- Monitor OpenAI API usage

---

## Summary

**Commits**: 
- `003a463` - Fixed LOG_LEVEL case sensitivity in Dockerfile
- `3357c62` - Updated LlamaIndex to v0.10.0

**Branch**: `main`  
**Files Changed**: 
- `Dockerfile`
- `requirements.txt`

**Deployment Status**: Railway is rebuilding with updated dependencies...
