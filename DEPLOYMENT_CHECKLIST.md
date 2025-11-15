# Local Deployment Pre-Flight Checklist

## ✅ Prerequisites Verified

### 1. Docker Installation
- [x] Docker installed: `Docker version 28.3.0`
- [ ] Docker daemon running
- [ ] Docker Compose available

### 2. Configuration Files
- [x] `.env` file created with:
  - `OPENAI_API_KEY=sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD`
  - `OPENAI_API_BASE=https://api.bltcy.ai`
  - `CHAT_MODEL=gpt-5-nano-2025-08-07`
  - `EMBEDDING_MODEL=text-embedding-3-small`
  - `DB_URL` configured for local PostgreSQL

### 3. Database Setup
- [ ] PostgreSQL container running
- [ ] pgvector extension available
- [ ] Database migrations applied

### 4. Application Files
- [x] `app/main.py` - FastAPI application
- [x] `app/config.py` - Configuration with custom API base URL support
- [x] `app/llama/setup.py` - LlamaIndex initialization with custom API base
- [x] `alembic/` - Database migrations
- [x] `Dockerfile` - Container build configuration
- [x] `docker-compose.yml` - Multi-container orchestration
- [x] `requirements.txt` - Python dependencies

## 🚨 Critical Issues to Check Before Starting

### Issue 1: Alembic URL Configuration
**Problem**: `alembic.ini` has placeholder URL
**Location**: Line in `alembic.ini`: `sqlalchemy.url = driver://user:pass@localhost/dbname`
**Status**: ⚠️ NEEDS FIX - But `alembic/env.py` overrides this with `DB_URL` env var
**Action**: Verify env.py properly loads DB_URL ✅

### Issue 2: Docker Compose Command
**Problem**: `docker-compose` command returned empty output
**Status**: ⚠️ NEEDS VERIFICATION
**Action**: Try `docker compose` (without hyphen) - newer Docker versions use this

### Issue 3: Database Connection String
**Problem**: Need to ensure correct format for asyncpg
**Current**: `postgresql://llamaindex:llamaindex123@localhost:5432/llamaindex_rag`
**Status**: ✅ Format is correct for asyncpg

### Issue 4: LlamaIndex PGVector Table
**Problem**: LlamaIndex creates its own `embeddings` table, not managed by Alembic
**Status**: ⚠️ NEEDS VERIFICATION
**Action**: Ensure pgvector extension is created before LlamaIndex initializes

## 📋 Step-by-Step Deployment Plan

### Step 1: Verify Docker
```bash
# Check Docker daemon is running
docker ps

# Check Docker Compose (try both commands)
docker compose version
docker-compose version
```

### Step 2: Start PostgreSQL Only (Test Database First)
```bash
# Start just the database
docker compose up postgres -d

# Wait for it to be healthy
docker compose ps

# Check logs
docker compose logs postgres
```

### Step 3: Verify Database Connection
```bash
# Connect to database to verify it's working
docker exec -it llamaindex_postgres psql -U llamaindex -d llamaindex_rag

# Inside psql, check pgvector extension
\dx

# Exit psql
\q
```

### Step 4: Run Database Migrations
```bash
# Install Python dependencies first (if running locally)
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Verify tables were created
docker exec -it llamaindex_postgres psql -U llamaindex -d llamaindex_rag -c "\dt"
```

### Step 5: Test API Configuration
```bash
# Test loading configuration
python -c "from app.config import load_config; c = load_config(); print(f'API Base: {c.openai_api_base}'); print(f'Chat Model: {c.chat_model}')"
```

### Step 6: Start the API
```bash
# Option A: Using Docker Compose (full stack)
docker compose up --build

# Option B: Local Python (database in Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Verify API is Running
```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

### Step 8: Run API Tests
```bash
# Run the test script
python test_api.py
```

## 🔍 Common Issues and Solutions

### Issue: "docker compose" command not found
**Solution**: Use `docker-compose` (with hyphen) or update Docker Desktop

### Issue: Port 5432 already in use
**Solution**: 
```bash
# Find what's using the port
netstat -ano | findstr :5432

# Stop existing PostgreSQL service or change port in docker-compose.yml
```

### Issue: "asyncpg.exceptions.InvalidCatalogNameError: database does not exist"
**Solution**: Database will be created automatically by the postgres container

### Issue: "pgvector extension not found"
**Solution**: Ensure using `pgvector/pgvector:pg16` image (already in docker-compose.yml)

### Issue: OpenAI API errors
**Solution**: 
- Verify API key is correct
- Verify base URL is accessible: `curl https://api.bltcy.ai`
- Check if the custom API supports the models specified

### Issue: Alembic can't connect to database
**Solution**: 
- Ensure DB_URL in .env is correct
- Verify PostgreSQL container is running
- Check alembic/env.py loads .env file correctly

## 🎯 Success Criteria

Before considering deployment successful, verify:

- [ ] PostgreSQL container is running and healthy
- [ ] pgvector extension is installed
- [ ] Database tables created (sessions, messages, documents)
- [ ] API starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Can create a session
- [ ] Can ingest a document
- [ ] Can query via chat endpoint
- [ ] Custom OpenAI API base URL is being used
- [ ] Logs show proper initialization

## 📝 Next Steps After Successful Local Test

1. Test with real documents
2. Test conversation history
3. Test error handling
4. Performance testing
5. Security review
6. Production deployment planning
