# Performance Optimization Guide

## Overview

This guide provides comprehensive performance optimization strategies for the LlamaIndex RAG API, covering database tuning, vector search optimization, LLM call optimization, and infrastructure scaling.

**Target Performance Metrics**:
- Chat response time: < 3 seconds (p95)
- Document ingestion: < 5 seconds per document
- Health check: < 100ms
- Error rate: < 1%
- Uptime: > 99.9%

---

## Table of Contents

1. [Database Optimization](#database-optimization)
2. [Vector Search Optimization](#vector-search-optimization)
3. [LLM Call Optimization](#llm-call-optimization)
4. [Application Optimization](#application-optimization)
5. [Infrastructure Scaling](#infrastructure-scaling)
6. [Caching Strategies](#caching-strategies)
7. [Monitoring & Profiling](#monitoring--profiling)

---

## Database Optimization

### 1. Connection Pooling

**Current Configuration** (`app/db/database.py`):
```python
pool = await asyncpg.create_pool(
    dsn=config.db_url,
    min_size=5,
    max_size=20
)
```

**Optimization Guidelines**:

| Scenario | Workers | min_size | max_size | Reasoning |
|----------|---------|----------|----------|-----------|
| Small (< 100 req/min) | 1-2 | 5 | 10 | Minimal overhead |
| Medium (100-1000 req/min) | 2-4 | 10 | 40 | Balance connections |
| Large (> 1000 req/min) | 4-8 | 20 | 80 | High concurrency |

**Formula**: `max_size = workers × 10`

**Tuning Parameters**:
```python
pool = await asyncpg.create_pool(
    dsn=config.db_url,
    min_size=10,              # Keep warm connections
    max_size=40,              # Maximum concurrent connections
    max_queries=50000,        # Recycle connections after N queries
    max_inactive_connection_lifetime=300,  # Close idle connections after 5 min
    command_timeout=60,       # Query timeout (seconds)
)
```

### 2. Query Optimization

**Indexes** (already implemented in migration):
```sql
-- Sessions
CREATE INDEX idx_sessions_last_active ON sessions(last_active_at);

-- Messages
CREATE INDEX idx_messages_session_created ON messages(session_id, created_at DESC);

-- Documents
CREATE INDEX idx_documents_created ON documents(created_at DESC);
```

**Additional Indexes** (if needed):
```sql
-- For user-based queries (future)
CREATE INDEX idx_sessions_user ON sessions(user_id) WHERE user_id IS NOT NULL;

-- For message role filtering
CREATE INDEX idx_messages_role ON messages(role);
```

**Query Performance Tips**:
- Use `EXPLAIN ANALYZE` to profile slow queries
- Limit result sets (already implemented with `MAX_HISTORY_MESSAGES`)
- Use pagination for large result sets
- Avoid `SELECT *` (already using specific columns)

### 3. Database Maintenance

**Regular Maintenance Tasks**:

```sql
-- Vacuum to reclaim space and update statistics
VACUUM ANALYZE sessions;
VACUUM ANALYZE messages;
VACUUM ANALYZE documents;

-- Reindex to rebuild indexes
REINDEX TABLE sessions;
REINDEX TABLE messages;
REINDEX TABLE documents;
```

**Automated Maintenance** (PostgreSQL):
```sql
-- Enable autovacuum (usually enabled by default)
ALTER TABLE sessions SET (autovacuum_enabled = true);
ALTER TABLE messages SET (autovacuum_enabled = true);
ALTER TABLE documents SET (autovacuum_enabled = true);
```

**Data Cleanup** (implement as scheduled job):
```sql
-- Delete old sessions (> 90 days inactive)
DELETE FROM sessions 
WHERE last_active_at < NOW() - INTERVAL '90 days';

-- Delete orphaned messages
DELETE FROM messages 
WHERE session_id NOT IN (SELECT id FROM sessions);
```

---

## Vector Search Optimization

### 1. Vector Index Types

**pgvector** supports two index types:

#### IVFFlat (Inverted File with Flat Compression)
- **Best for**: < 1M vectors
- **Pros**: Faster build time, good recall
- **Cons**: Slower queries than HNSW

```sql
CREATE INDEX ON embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**Tuning `lists` parameter**:
- Small datasets (< 100K): `lists = 100`
- Medium datasets (100K-1M): `lists = 1000`
- Large datasets (> 1M): `lists = 10000`
- Formula: `lists = rows / 1000` (approximate)

#### HNSW (Hierarchical Navigable Small World)
- **Best for**: > 1M vectors
- **Pros**: Faster queries, better recall
- **Cons**: Slower build time, more memory

```sql
CREATE INDEX ON embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

**Tuning parameters**:
- `m`: Number of connections (default: 16)
  - Higher = better recall, more memory
  - Recommended: 16-32
- `ef_construction`: Build-time search depth (default: 64)
  - Higher = better recall, slower build
  - Recommended: 64-128

### 2. Query-Time Optimization

**Adjust `top_k` parameter**:
```python
# In ChatRequest
class ChatConfig(BaseModel):
    top_k: int = 5  # Lower = faster, higher = more context
    temperature: float = 0.3
```

**Performance vs. Quality Trade-off**:

| top_k | Query Time | Context Quality | Use Case |
|-------|------------|-----------------|----------|
| 3 | ~100ms | Good | Fast responses |
| 5 | ~150ms | Better | Balanced (default) |
| 10 | ~250ms | Best | Maximum context |

**HNSW Query-Time Tuning**:
```sql
-- Set search depth for current session
SET hnsw.ef_search = 40;  -- Default: 40

-- Higher = better recall, slower queries
-- Recommended: 40-100
```

### 3. Embedding Optimization

**Model Selection**:

| Model | Dimensions | Speed | Quality | Cost |
|-------|------------|-------|---------|------|
| text-embedding-3-small | 1536 | Fast | Good | Low |
| text-embedding-3-large | 3072 | Slow | Better | High |
| text-embedding-ada-002 | 1536 | Fast | Good | Medium |

**Recommendation**: Use `text-embedding-3-small` (default) for best speed/quality balance.

**Chunking Strategy**:
```python
# LlamaIndex default chunking
chunk_size = 1024  # tokens
chunk_overlap = 20  # tokens

# Optimization options:
# - Smaller chunks = more precise retrieval, more chunks to search
# - Larger chunks = more context per chunk, fewer chunks to search
```

---

## LLM Call Optimization

### 1. Model Selection

**OpenAI Models**:

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| gpt-3.5-turbo | Fast | Good | Low | High-volume |
| gpt-4-turbo | Medium | Better | Medium | Balanced |
| gpt-4 | Slow | Best | High | Quality-critical |

**Custom Models** (via `OPENAI_API_BASE`):
- Test performance and quality
- May offer better speed or cost

### 2. Timeout Configuration

**Current Implementation** (`app/retry_utils.py`):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, Timeout)),
)
```

**Optimization**:
```python
# Adjust timeout in OpenAI client
llm = OpenAI(
    model=config.chat_model,
    temperature=temperature,
    timeout=30.0,  # Reduce from default 60s
    max_retries=2,  # Reduce retries for faster failure
)
```

### 3. Context Window Management

**Reduce Context Size**:
```python
# In config
MAX_HISTORY_MESSAGES=10  # Default

# Optimization options:
# - Fewer messages = faster, less context
# - More messages = slower, better context
```

**Context Size Impact**:

| Messages | Tokens | Latency | Cost |
|----------|--------|---------|------|
| 5 | ~1000 | Low | Low |
| 10 | ~2000 | Medium | Medium |
| 20 | ~4000 | High | High |

### 4. Temperature Tuning

```python
DEFAULT_TEMPERATURE=0.3  # Default

# Lower temperature = faster, more deterministic
# Higher temperature = slower, more creative
```

**Recommendation**: Keep at 0.3 for balanced performance.

### 5. Streaming Responses (Future Enhancement)

**Benefits**:
- Perceived latency reduction
- Better user experience
- No actual speed improvement

**Implementation** (future):
```python
async def chat_stream(message: str):
    response = await llm.astream_chat(message)
    async for chunk in response:
        yield chunk
```

---

## Application Optimization

### 1. Worker Configuration

**Uvicorn Workers**:
```bash
WORKERS=2  # Default for production

# Formula: workers = (2 × CPU cores) + 1
# Examples:
# - 1 CPU: 3 workers
# - 2 CPU: 5 workers
# - 4 CPU: 9 workers
```

**Trade-offs**:
- More workers = handle more concurrent requests
- More workers = more memory usage
- More workers = more database connections needed

**Monitoring**:
```bash
# Check worker CPU usage
top -p $(pgrep -f uvicorn)

# If CPU < 50%, increase workers
# If CPU > 90%, decrease workers or scale horizontally
```

### 2. Async Operations

**Already Optimized**:
- All database operations are async (`asyncpg`)
- All service methods are async
- FastAPI handles async natively

**Best Practices**:
- Use `await` for I/O operations
- Don't block the event loop
- Use `asyncio.gather()` for parallel operations

### 3. Memory Management

**Monitor Memory Usage**:
```bash
# Check memory usage
docker stats llamaindex-rag-api

# If memory usage > 80%, optimize:
# - Reduce WORKERS
# - Reduce database pool size
# - Reduce MAX_HISTORY_MESSAGES
```

**Memory Optimization**:
```python
# In LlamaIndex setup
Settings.chunk_size = 1024  # Reduce if memory constrained
Settings.chunk_overlap = 20  # Reduce overlap
```

### 4. Request Timeout

**Current Configuration**:
```bash
REQUEST_TIMEOUT=60  # seconds
```

**Optimization**:
```bash
# Reduce timeout for faster failure
REQUEST_TIMEOUT=30

# Or increase for complex queries
REQUEST_TIMEOUT=120
```

---

## Infrastructure Scaling

### 1. Vertical Scaling

**When to Scale Up**:
- CPU usage consistently > 80%
- Memory usage consistently > 80%
- Response times increasing

**Railway Scaling**:
- Increase memory/CPU in service settings
- Monitor performance after scaling
- Adjust `WORKERS` accordingly

### 2. Horizontal Scaling

**When to Scale Out**:
- Vertical scaling no longer effective
- Need high availability
- Traffic exceeds single instance capacity

**Implementation**:
- Deploy multiple instances
- Use load balancer (Railway provides this)
- Ensure database can handle connections

**Load Balancer Configuration**:
- Health check: `/health`
- Algorithm: Round-robin or least connections
- Session affinity: Not required (stateless API)

### 3. Database Scaling

**Read Replicas**:
- For read-heavy workloads
- Route read queries to replicas
- Write queries to primary

**Connection Pooling**:
- Use PgBouncer for connection pooling
- Reduces database connection overhead

**Sharding** (if needed):
- Shard by user_id or session_id
- Complex implementation, only for very large scale

---

## Caching Strategies

### 1. Response Caching (Future Enhancement)

**Cache Candidates**:
- Identical queries (with TTL)
- Frequently accessed documents
- Session metadata

**Implementation Options**:
- Redis for distributed caching
- In-memory cache for single instance

**Example** (Redis):
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def cache_response(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 2. Embedding Caching

**Cache Embeddings**:
- Store embeddings for repeated text
- Reduces OpenAI API calls
- Significant cost savings

**Implementation**:
```python
# Check if text already embedded
existing_embedding = await db.fetch(
    "SELECT embedding FROM embedding_cache WHERE text_hash = $1",
    hash(text)
)

if existing_embedding:
    return existing_embedding
else:
    embedding = await embed_model.get_embedding(text)
    await db.execute(
        "INSERT INTO embedding_cache (text_hash, embedding) VALUES ($1, $2)",
        hash(text), embedding
    )
    return embedding
```

### 3. Session Caching

**Cache Session Data**:
- Reduce database queries for active sessions
- Use Redis or in-memory cache

**Implementation**:
```python
# Cache session for 5 minutes
session = cache.get(f"session:{session_id}")
if not session:
    session = await db.fetch_session(session_id)
    cache.set(f"session:{session_id}", session, ttl=300)
```

---

## Monitoring & Profiling

### 1. Key Metrics to Monitor

**Application Metrics**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Active connections

**Database Metrics**:
- Query time (p50, p95, p99)
- Connection pool usage
- Cache hit rate
- Slow queries

**Infrastructure Metrics**:
- CPU usage (%)
- Memory usage (%)
- Network I/O
- Disk I/O

**OpenAI API Metrics**:
- API latency
- Token usage
- Cost per request
- Rate limit hits

### 2. Profiling Tools

**Python Profiling**:
```python
# cProfile for CPU profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

**Memory Profiling**:
```python
# memory_profiler
from memory_profiler import profile

@profile
async def my_function():
    # ... code to profile ...
    pass
```

**Database Profiling**:
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 3. Load Testing

**Tools**:
- Locust (Python-based)
- k6 (JavaScript-based)
- Apache JMeter
- Artillery

**Locust Example**:
```python
from locust import HttpUser, task, between

class RAGAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def chat(self):
        self.client.post("/chat", json={
            "session_id": "test",
            "message": "What is the capital of France?"
        })
    
    @task(1)
    def ingest(self):
        self.client.post("/ingest", json={
            "text": "Test document content",
            "title": "Test"
        })
```

**Run Load Test**:
```bash
# Install locust
pip install locust

# Run test
locust -f locustfile.py --host=https://your-api.railway.app

# Open browser to http://localhost:8089
# Configure users and spawn rate
```

### 4. Monitoring Setup

**Recommended Tools**:
- **Sentry**: Error tracking
- **Datadog**: Full-stack monitoring
- **Prometheus + Grafana**: Custom metrics
- **Railway Metrics**: Built-in monitoring

**Custom Metrics** (Prometheus example):
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Instrument code
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response

# Expose metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Performance Benchmarks

### Target Benchmarks

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Chat response (p95) | < 3s | < 5s | > 5s |
| Ingest time | < 5s | < 10s | > 10s |
| Health check | < 100ms | < 500ms | > 500ms |
| Error rate | < 0.1% | < 1% | > 1% |
| Uptime | > 99.9% | > 99% | < 99% |

### Baseline Performance

**Test Environment**:
- 1 worker
- 2 CPU cores
- 4GB RAM
- PostgreSQL with 100K vectors

**Results** (approximate):
- Chat response: 2-4 seconds (p95)
- Ingest time: 3-6 seconds
- Health check: 50-100ms
- Throughput: 10-20 requests/second

### Optimization Impact

| Optimization | Impact | Effort |
|--------------|--------|--------|
| Vector index (HNSW) | -30% latency | Low |
| Reduce top_k (5→3) | -20% latency | Low |
| Increase workers (1→4) | +300% throughput | Low |
| Database connection pool tuning | +10% throughput | Low |
| Response caching | -50% latency (cached) | Medium |
| Embedding caching | -80% ingest time (cached) | Medium |
| Horizontal scaling (2x instances) | +100% throughput | High |

---

## Optimization Checklist

### Quick Wins (Low Effort, High Impact)

- [ ] Enable HNSW vector index
- [ ] Tune database connection pool
- [ ] Adjust `WORKERS` based on CPU cores
- [ ] Reduce `top_k` if acceptable
- [ ] Set appropriate `REQUEST_TIMEOUT`
- [ ] Enable query result caching

### Medium Effort Optimizations

- [ ] Implement response caching (Redis)
- [ ] Implement embedding caching
- [ ] Add database read replicas
- [ ] Optimize slow queries
- [ ] Implement session caching

### Long-Term Optimizations

- [ ] Horizontal scaling with load balancer
- [ ] Implement streaming responses
- [ ] Database sharding (if needed)
- [ ] CDN for static assets
- [ ] Advanced caching strategies

---

## Troubleshooting Performance Issues

### Slow Response Times

**Diagnosis**:
1. Check OpenAI API latency
2. Check database query times
3. Check vector search performance
4. Check CPU/memory usage

**Solutions**:
- Reduce `top_k`
- Reduce `MAX_HISTORY_MESSAGES`
- Optimize vector index
- Scale infrastructure

### High Error Rates

**Diagnosis**:
1. Check application logs
2. Check OpenAI API status
3. Check database connection pool
4. Check memory usage

**Solutions**:
- Increase timeout values
- Increase connection pool size
- Add retry logic
- Scale infrastructure

### High Latency Spikes

**Diagnosis**:
1. Check for cold starts
2. Check for database connection exhaustion
3. Check for memory pressure
4. Check for rate limiting

**Solutions**:
- Keep connections warm
- Increase connection pool
- Increase memory allocation
- Implement backpressure

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Next Review Date**: 2025-04-15
