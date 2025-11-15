# Monitoring & Alerting Guide

## Overview

This guide provides comprehensive monitoring and alerting strategies for the LlamaIndex RAG API in production environments.

**Monitoring Goals**:
- Detect issues before users are impacted
- Understand system performance and behavior
- Enable data-driven optimization decisions
- Support incident response and debugging

---

## Table of Contents

1. [Health Checks](#health-checks)
2. [Application Metrics](#application-metrics)
3. [Infrastructure Metrics](#infrastructure-metrics)
4. [Log Management](#log-management)
5. [Alerting Strategy](#alerting-strategy)
6. [Monitoring Tools](#monitoring-tools)
7. [Dashboards](#dashboards)

---

## Health Checks

### 1. Application Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Monitoring**:
- Check every 30 seconds
- Alert if 3 consecutive failures
- Expected response time: < 100ms

**Railway Configuration**:
```yaml
# Railway automatically monitors /health
healthCheckPath: /health
healthCheckTimeout: 10
```

**External Monitoring** (UptimeRobot, Pingdom):
```
URL: https://your-api.railway.app/health
Interval: 60 seconds
Timeout: 10 seconds
Alert: Email/SMS on failure
```

### 2. Database Health Check

**Manual Check**:
```bash
# Test database connection
psql $DB_URL -c "SELECT 1;"

# Check pgvector extension
psql $DB_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Automated Check** (add to health endpoint):
```python
@router.get("/health/detailed")
async def detailed_health_check():
    checks = {
        "api": "ok",
        "database": "unknown",
        "openai": "unknown"
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "error"
        logger.error(f"Database health check failed: {e}")
    
    # Check OpenAI (optional)
    try:
        # Simple API call
        checks["openai"] = "ok"
    except Exception as e:
        checks["openai"] = "error"
        logger.error(f"OpenAI health check failed: {e}")
    
    status_code = 200 if all(v == "ok" for v in checks.values()) else 503
    return JSONResponse(status_code=status_code, content=checks)
```

### 3. Dependency Health Checks

**OpenAI API Status**:
- Monitor: https://status.openai.com
- Subscribe to status updates
- Check API latency regularly

**Database Status**:
- Monitor connection pool usage
- Check for connection leaks
- Monitor query performance

---

## Application Metrics

### 1. Request Metrics

**Key Metrics**:
- **Request Rate**: Requests per second
- **Response Time**: p50, p95, p99 latency
- **Error Rate**: Percentage of failed requests
- **Status Codes**: Distribution of HTTP status codes

**Implementation** (Prometheus example):
```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Response time histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Active requests gauge
http_requests_active = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    http_requests_active.inc()
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    finally:
        http_requests_active.dec()
```

### 2. Business Metrics

**Key Metrics**:
- **Chat Requests**: Total chat requests per hour/day
- **Documents Ingested**: Total documents ingested per hour/day
- **Active Sessions**: Number of active sessions
- **Messages per Session**: Average messages per session
- **Token Usage**: Total tokens consumed (OpenAI)

**Implementation**:
```python
# Business metrics
chat_requests_total = Counter('chat_requests_total', 'Total chat requests')
documents_ingested_total = Counter('documents_ingested_total', 'Total documents ingested')
active_sessions = Gauge('active_sessions', 'Number of active sessions')
tokens_used_total = Counter('tokens_used_total', 'Total tokens used', ['model'])

# In chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    chat_requests_total.inc()
    # ... rest of implementation
    
# In ingest endpoint
@app.post("/ingest")
async def ingest(request: IngestRequest):
    documents_ingested_total.inc()
    # ... rest of implementation
```

### 3. Error Metrics

**Key Metrics**:
- **Error Rate**: Percentage of requests resulting in errors
- **Error Types**: Distribution of error types
- **OpenAI Errors**: Rate of OpenAI API errors
- **Database Errors**: Rate of database errors

**Implementation**:
```python
# Error counter
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# In exception handlers
@app.exception_handler(OpenAIServiceError)
async def openai_error_handler(request: Request, exc: OpenAIServiceError):
    errors_total.labels(
        error_type='openai_error',
        endpoint=request.url.path
    ).inc()
    # ... rest of handler
```

### 4. Performance Metrics

**Key Metrics**:
- **Vector Search Time**: Time spent on vector search
- **LLM Response Time**: Time spent waiting for LLM
- **Database Query Time**: Time spent on database queries
- **Total Request Time**: End-to-end request time

**Implementation**:
```python
# Performance histograms
vector_search_duration = Histogram('vector_search_duration_seconds', 'Vector search duration')
llm_response_duration = Histogram('llm_response_duration_seconds', 'LLM response duration')
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')

# In service methods
async def generate_response(self, message: str, ...):
    # Vector search timing
    start = time.time()
    results = await self.index.query(message)
    vector_search_duration.observe(time.time() - start)
    
    # LLM timing
    start = time.time()
    response = await self.llm.generate(message)
    llm_response_duration.observe(time.time() - start)
    
    return response
```

---

## Infrastructure Metrics

### 1. System Metrics

**Key Metrics**:
- **CPU Usage**: Percentage of CPU used
- **Memory Usage**: Percentage of memory used
- **Disk Usage**: Percentage of disk used
- **Network I/O**: Bytes sent/received

**Railway Monitoring**:
- Built-in metrics dashboard
- CPU, memory, network graphs
- Real-time and historical data

**Custom Monitoring**:
```python
import psutil

# System metrics
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('disk_usage_percent', 'Disk usage percentage')

# Update metrics periodically
@app.on_event("startup")
async def start_system_metrics():
    async def update_metrics():
        while True:
            cpu_usage.set(psutil.cpu_percent())
            memory_usage.set(psutil.virtual_memory().percent)
            disk_usage.set(psutil.disk_usage('/').percent)
            await asyncio.sleep(60)
    
    asyncio.create_task(update_metrics())
```

### 2. Database Metrics

**Key Metrics**:
- **Connection Pool Usage**: Active/idle connections
- **Query Performance**: Query execution time
- **Cache Hit Rate**: Database cache effectiveness
- **Database Size**: Total database size

**PostgreSQL Queries**:
```sql
-- Connection pool usage
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity
WHERE datname = 'llamaindex_rag';

-- Slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- queries > 1 second
ORDER BY mean_time DESC
LIMIT 10;

-- Database size
SELECT pg_size_pretty(pg_database_size('llamaindex_rag'));

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Cache hit rate
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;
```

**Monitoring Implementation**:
```python
# Database metrics
db_connections_active = Gauge('db_connections_active', 'Active database connections')
db_connections_idle = Gauge('db_connections_idle', 'Idle database connections')
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')

# Update periodically
async def update_db_metrics():
    result = await db.fetch("""
        SELECT 
            count(*) FILTER (WHERE state = 'active') as active,
            count(*) FILTER (WHERE state = 'idle') as idle
        FROM pg_stat_activity
        WHERE datname = current_database()
    """)
    db_connections_active.set(result[0]['active'])
    db_connections_idle.set(result[0]['idle'])
```

### 3. OpenAI API Metrics

**Key Metrics**:
- **API Latency**: Time to receive response
- **Token Usage**: Tokens consumed per request
- **API Errors**: Rate of API errors
- **Cost**: Estimated cost per request

**Implementation**:
```python
# OpenAI metrics
openai_api_duration = Histogram('openai_api_duration_seconds', 'OpenAI API duration', ['operation'])
openai_tokens_used = Counter('openai_tokens_used_total', 'OpenAI tokens used', ['model', 'type'])
openai_api_errors = Counter('openai_api_errors_total', 'OpenAI API errors', ['error_type'])

# In LLM calls
async def generate_response(self, message: str):
    start = time.time()
    try:
        response = await self.llm.generate(message)
        duration = time.time() - start
        
        openai_api_duration.labels(operation='chat').observe(duration)
        openai_tokens_used.labels(
            model=self.config.chat_model,
            type='completion'
        ).inc(response.usage.completion_tokens)
        openai_tokens_used.labels(
            model=self.config.chat_model,
            type='prompt'
        ).inc(response.usage.prompt_tokens)
        
        return response
    except Exception as e:
        openai_api_errors.labels(error_type=type(e).__name__).inc()
        raise
```

---

## Log Management

### 1. Structured Logging

**Current Implementation** (`app/logging_config.py`):
```python
# Structured log format
log_data = {
    "timestamp": "2025-01-15 10:30:45",
    "level": "INFO",
    "logger": "app.main",
    "message": "Starting up RAG API Server",
    "version": "0.1.0",
    "environment": "production"
}
```

**Log Levels**:
- **DEBUG**: Detailed debugging (development only)
- **INFO**: General information (production default)
- **WARNING**: Warning messages (production recommended)
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

**Production Configuration**:
```bash
LOG_LEVEL=INFO  # or WARNING for less verbose
```

### 2. Log Aggregation

**Recommended Tools**:
- **Railway Logs**: Built-in log viewer
- **Datadog**: Full-stack monitoring with logs
- **Elasticsearch + Kibana**: Self-hosted log aggregation
- **Splunk**: Enterprise log management
- **Papertrail**: Simple log aggregation

**Log Shipping** (example with Datadog):
```python
import logging
from datadog import initialize, statsd

# Initialize Datadog
initialize(api_key='your_api_key', app_key='your_app_key')

# Configure logging handler
handler = logging.handlers.DatadogLogHandler(
    api_key='your_api_key',
    hostname='your-api.railway.app'
)
logger.addHandler(handler)
```

### 3. Log Retention

**Recommendations**:
- **Development**: 7 days
- **Staging**: 30 days
- **Production**: 90 days (or per compliance requirements)

**Railway**: Logs retained for 7 days on free tier, longer on paid tiers

### 4. Log Analysis

**Key Patterns to Monitor**:
- Error rate trends
- Slow query patterns
- OpenAI API failures
- Database connection issues
- Memory warnings

**Example Queries** (Elasticsearch):
```json
// Error rate over time
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": { "timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "errors_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "interval": "5m"
      }
    }
  }
}

// Top error messages
{
  "query": {
    "match": { "level": "ERROR" }
  },
  "aggs": {
    "top_errors": {
      "terms": {
        "field": "message.keyword",
        "size": 10
      }
    }
  }
}
```

---

## Alerting Strategy

### 1. Alert Levels

**Critical** (Immediate Response):
- Service down (health check failing)
- Error rate > 10%
- Database connection failures
- Memory usage > 95%

**Warning** (Response within 1 hour):
- Error rate > 5%
- Response time p95 > 5 seconds
- Memory usage > 80%
- CPU usage > 80%

**Info** (Response within 24 hours):
- Error rate > 1%
- Response time p95 > 3 seconds
- Disk usage > 80%

### 2. Alert Rules

**Health Check Alerts**:
```yaml
# UptimeRobot configuration
- name: API Health Check
  url: https://your-api.railway.app/health
  interval: 60  # seconds
  alert_contacts:
    - email: ops@example.com
    - sms: +1234567890
  alert_threshold: 3  # failures before alert
```

**Error Rate Alerts**:
```yaml
# Prometheus alert rule
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} (threshold: 0.05)"
```

**Response Time Alerts**:
```yaml
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Slow response time detected"
    description: "p95 response time is {{ $value }}s (threshold: 5s)"
```

**Resource Alerts**:
```yaml
- alert: HighMemoryUsage
  expr: memory_usage_percent > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage"
    description: "Memory usage is {{ $value }}% (threshold: 80%)"

- alert: CriticalMemoryUsage
  expr: memory_usage_percent > 95
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Critical memory usage"
    description: "Memory usage is {{ $value }}% (threshold: 95%)"
```

**Database Alerts**:
```yaml
- alert: DatabaseConnectionPoolExhausted
  expr: db_connections_active / db_connections_max > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool nearly exhausted"
    description: "{{ $value }}% of connections in use"
```

### 3. Alert Channels

**Recommended Channels**:
- **Email**: For all alerts
- **SMS**: For critical alerts only
- **Slack**: For team notifications
- **PagerDuty**: For on-call rotation
- **Webhook**: For custom integrations

**Example Slack Integration**:
```python
import requests

def send_slack_alert(message, severity='info'):
    webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    
    color = {
        'critical': 'danger',
        'warning': 'warning',
        'info': 'good'
    }[severity]
    
    payload = {
        'attachments': [{
            'color': color,
            'title': f'{severity.upper()}: RAG API Alert',
            'text': message,
            'ts': int(time.time())
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

### 4. Alert Fatigue Prevention

**Best Practices**:
- Set appropriate thresholds (not too sensitive)
- Use alert grouping (combine similar alerts)
- Implement alert suppression during maintenance
- Review and adjust alerts regularly
- Use escalation policies (warning → critical)

**Alert Grouping Example**:
```yaml
# Group alerts by service and severity
route:
  group_by: ['service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
```

---

## Monitoring Tools

### 1. Railway Built-in Monitoring

**Features**:
- CPU, memory, network graphs
- Real-time metrics
- Log viewer
- Deployment history

**Access**: Railway dashboard → Your service → Metrics tab

### 2. Prometheus + Grafana

**Setup**:
```bash
# Install Prometheus client
pip install prometheus-client

# Expose metrics endpoint
from prometheus_client import generate_latest

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**Prometheus Configuration** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'rag-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['your-api.railway.app']
    metrics_path: '/metrics'
```

**Grafana Dashboard**:
- Import pre-built dashboards
- Create custom dashboards
- Set up alerts

### 3. Datadog

**Setup**:
```bash
# Install Datadog client
pip install datadog

# Initialize
from datadog import initialize, statsd

initialize(api_key='your_api_key')

# Send metrics
statsd.increment('rag_api.requests')
statsd.histogram('rag_api.response_time', 0.5)
```

**Features**:
- Full-stack monitoring
- APM (Application Performance Monitoring)
- Log aggregation
- Custom dashboards
- Alerting

### 4. Sentry

**Setup**:
```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]

# Initialize in app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    environment="production"
)
```

**Features**:
- Error tracking
- Performance monitoring
- Release tracking
- User feedback
- Issue assignment

### 5. New Relic

**Setup**:
```bash
# Install New Relic agent
pip install newrelic

# Run with agent
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn app.main:app
```

**Features**:
- APM
- Infrastructure monitoring
- Log management
- Alerting

---

## Dashboards

### 1. Overview Dashboard

**Key Metrics**:
- Request rate (requests/second)
- Error rate (%)
- Response time (p50, p95, p99)
- Active sessions
- System health (CPU, memory)

**Grafana Panel Example**:
```json
{
  "title": "Request Rate",
  "targets": [{
    "expr": "rate(http_requests_total[5m])",
    "legendFormat": "{{method}} {{endpoint}}"
  }],
  "type": "graph"
}
```

### 2. Performance Dashboard

**Key Metrics**:
- Vector search time
- LLM response time
- Database query time
- Total request time
- Throughput

### 3. Error Dashboard

**Key Metrics**:
- Error rate over time
- Error types distribution
- Top error messages
- Failed requests by endpoint

### 4. Infrastructure Dashboard

**Key Metrics**:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Database connections

### 5. Business Dashboard

**Key Metrics**:
- Total chat requests
- Total documents ingested
- Active users/sessions
- Token usage
- Estimated costs

---

## Monitoring Checklist

### Initial Setup

- [ ] Health check endpoint configured
- [ ] Uptime monitoring enabled (UptimeRobot, Pingdom)
- [ ] Log aggregation configured
- [ ] Metrics collection enabled
- [ ] Dashboards created
- [ ] Alerts configured
- [ ] Alert channels set up (email, Slack, SMS)
- [ ] On-call rotation defined

### Daily Monitoring

- [ ] Check error rates
- [ ] Review slow queries
- [ ] Monitor resource usage
- [ ] Check OpenAI API usage and costs
- [ ] Review alerts

### Weekly Monitoring

- [ ] Review performance trends
- [ ] Analyze error patterns
- [ ] Check database growth
- [ ] Review and adjust alerts
- [ ] Update dashboards

### Monthly Monitoring

- [ ] Performance review
- [ ] Cost analysis
- [ ] Capacity planning
- [ ] Security review
- [ ] Update monitoring tools

---

## Incident Response

### 1. Incident Detection

**Sources**:
- Automated alerts
- User reports
- Monitoring dashboards
- Log analysis

### 2. Incident Response Process

1. **Acknowledge**: Acknowledge alert, assign owner
2. **Assess**: Determine severity and impact
3. **Communicate**: Notify stakeholders
4. **Investigate**: Review logs, metrics, traces
5. **Mitigate**: Apply temporary fix
6. **Resolve**: Implement permanent fix
7. **Document**: Write post-mortem
8. **Improve**: Implement preventive measures

### 3. Incident Severity Levels

**SEV1 (Critical)**:
- Service completely down
- Data loss or corruption
- Security breach
- Response: Immediate, all hands on deck

**SEV2 (High)**:
- Partial service degradation
- High error rates (> 10%)
- Performance severely impacted
- Response: Within 1 hour

**SEV3 (Medium)**:
- Minor service degradation
- Moderate error rates (1-10%)
- Performance moderately impacted
- Response: Within 4 hours

**SEV4 (Low)**:
- Minimal impact
- Low error rates (< 1%)
- Minor performance issues
- Response: Within 24 hours

### 4. Post-Mortem Template

```markdown
# Incident Post-Mortem

## Summary
Brief description of the incident

## Timeline
- HH:MM - Event 1
- HH:MM - Event 2
- HH:MM - Resolution

## Impact
- Duration: X hours
- Affected users: X
- Error rate: X%
- Revenue impact: $X

## Root Cause
Detailed explanation of what caused the incident

## Resolution
How the incident was resolved

## Action Items
- [ ] Action 1 (Owner: Name, Due: Date)
- [ ] Action 2 (Owner: Name, Due: Date)

## Lessons Learned
What we learned and how to prevent similar incidents
```

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Next Review Date**: 2025-04-15
