# Quick Start Guide

## 🚀 Fastest Way to Test

### Step 1: Run Setup Verification
```bash
python setup_local.py
```

### Step 2: Start Services
```bash
docker compose up --build
```

### Step 3: Test API (in new terminal)
```bash
python test_api.py
```

## 📋 Manual Testing Commands

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Session
```bash
curl -X POST http://localhost:8000/api/v1/sessions
```

### Ingest Document
```bash
curl -X POST "http://localhost:8000/api/v1/ingest?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d "{\"content\": \"LlamaIndex is a framework for LLM applications.\", \"metadata\": {\"source\": \"test\"}}"
```

### Chat
```bash
curl -X POST "http://localhost:8000/api/v1/chat?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is LlamaIndex?\"}"
```

## 🛑 Stop Services
```bash
docker compose down
```

## 🔄 Restart Services
```bash
docker compose restart
```

## 📊 View Logs
```bash
# All services
docker compose logs -f

# Just API
docker compose logs -f api

# Just database
docker compose logs -f postgres
```

## 🧹 Clean Up Everything
```bash
# Stop and remove containers, networks
docker compose down

# Also remove volumes (deletes database data)
docker compose down -v
```

## 🔍 Debug Commands

### Check Running Containers
```bash
docker ps
```

### Connect to Database
```bash
docker exec -it llamaindex_postgres psql -U llamaindex -d llamaindex_rag
```

### Check Database Tables
```bash
docker exec -it llamaindex_postgres psql -U llamaindex -d llamaindex_rag -c "\dt"
```

### View API Container Logs
```bash
docker logs llamaindex_api
```

### Rebuild Without Cache
```bash
docker compose build --no-cache
docker compose up
```

## 📖 API Documentation
Once running, visit: http://localhost:8000/docs
