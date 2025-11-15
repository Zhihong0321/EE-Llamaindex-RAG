# End-to-End (E2E) Tests

## Overview

This directory contains end-to-end tests that verify the complete RAG API system is production-ready. These tests run against a live deployment and validate the entire workflow from document ingestion to chat responses.

## Test Suite

### 1. Full RAG Workflow (`test_full_workflow.py`)

Tests the complete RAG pipeline:
- ✅ Health check
- ✅ Document ingestion (multiple documents)
- ✅ Chat with RAG (retrieves context from documents)
- ✅ Source retrieval and metadata
- ✅ Follow-up questions
- ✅ Document listing

**Requirements Tested**: 2.1-2.7, 5.1-5.9, 9.1-9.3

### 2. Multi-Turn Conversation (`test_multi_turn_conversation.py`)

Tests conversation context preservation:
- ✅ Multiple conversation turns
- ✅ Context maintained across turns
- ✅ Follow-up questions work correctly
- ✅ Chat history is preserved
- ✅ Pronoun resolution ("it", "they", etc.)

**Requirements Tested**: 3.1-3.4, 4.1-4.5, 5.1-5.9

### 3. Session Isolation (`test_session_isolation.py`)

Tests that sessions are properly isolated:
- ✅ Different sessions maintain separate histories
- ✅ No message leakage between sessions
- ✅ Independent context per session
- ✅ New sessions have no prior context
- ✅ Session security boundaries

**Requirements Tested**: 3.1-3.4, 4.1-4.5

### 4. Source Retrieval Accuracy (`test_source_accuracy.py`)

Tests source retrieval quality:
- ✅ Relevant sources are retrieved
- ✅ Source metadata is accurate (document_id, title, snippet, score)
- ✅ Relevance scores are reasonable
- ✅ Scores are properly ordered (descending)
- ✅ Snippets are meaningful
- ✅ top_k parameter works correctly

**Requirements Tested**: 2.6, 5.4, 5.5, 5.9

## Prerequisites

### 1. Running API Server

The E2E tests require a running instance of the RAG API:

```bash
# Start with Docker Compose
docker compose up --build

# Or start manually
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Environment Configuration

Ensure your `.env` file is properly configured:

```bash
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.bltcy.ai  # Optional: custom API endpoint
DB_URL=postgresql://llamaindex:llamaindex123@localhost:5432/llamaindex_rag
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-5-nano-2025-08-07
```

### 3. Database

PostgreSQL with pgvector extension must be running and accessible.

## Running Tests

### Run All E2E Tests

```bash
# From project root
python tests/e2e/run_all_e2e_tests.py
```

This will:
1. Run all 4 E2E test suites in sequence
2. Provide detailed output for each test
3. Generate a comprehensive summary
4. Assess production readiness

### Run Individual Tests

```bash
# Full workflow test
python tests/e2e/test_full_workflow.py

# Multi-turn conversation test
python tests/e2e/test_multi_turn_conversation.py

# Session isolation test
python tests/e2e/test_session_isolation.py

# Source accuracy test
python tests/e2e/test_source_accuracy.py
```

### Run with Pytest

```bash
# Run all E2E tests
pytest tests/e2e/ -v -s

# Run specific test
pytest tests/e2e/test_full_workflow.py -v -s
```

## Expected Output

### Successful Test Run

```
==============================================================================
  END-TO-END PRODUCTION READINESS TESTS
==============================================================================
Started at: 2025-01-15 10:30:00

==============================================================================
  Running: Full RAG Workflow
==============================================================================
[1/6] Checking API health...
✅ API is healthy
[2/6] Ingesting document 1 (LlamaIndex)...
✅ Document 1 ingested: abc-123
...
✅ FULL RAG WORKFLOW TEST PASSED

==============================================================================
  TEST SUMMARY
==============================================================================

Total Tests: 4
Passed: 4 ✅
Failed: 0 ❌
Total Time: 45.23s

Detailed Results:
  ✅ PASS - Full RAG Workflow (12.34s)
  ✅ PASS - Multi-Turn Conversation (10.56s)
  ✅ PASS - Session Isolation (15.78s)
  ✅ PASS - Source Retrieval Accuracy (6.55s)

==============================================================================
  PRODUCTION READINESS ASSESSMENT
==============================================================================

🎉 ALL TESTS PASSED!

✅ System is PRODUCTION READY

The RAG API has successfully passed all end-to-end tests:
  ✅ Full workflow (ingest → chat → retrieve)
  ✅ Multi-turn conversations with context
  ✅ Session isolation and security
  ✅ Source retrieval accuracy

You can proceed with production deployment.
```

## Test Data

The E2E tests create their own test data:
- Documents are ingested during test execution
- Unique session IDs are generated (e.g., `e2e-test-{uuid}`)
- Test data is self-contained within each test

## Cleanup

E2E tests do NOT automatically clean up test data. To clean the database:

```bash
# Connect to database
psql postgresql://llamaindex:llamaindex123@localhost:5432/llamaindex_rag

# Delete test data
DELETE FROM messages WHERE session_id LIKE 'e2e-test-%';
DELETE FROM messages WHERE session_id LIKE 'session-a-%';
DELETE FROM messages WHERE session_id LIKE 'session-b-%';
DELETE FROM messages WHERE session_id LIKE 'multi-turn-%';
DELETE FROM messages WHERE session_id LIKE 'source-test-%';
DELETE FROM sessions WHERE id LIKE 'e2e-test-%';
DELETE FROM sessions WHERE id LIKE 'session-a-%';
DELETE FROM sessions WHERE id LIKE 'session-b-%';
DELETE FROM sessions WHERE id LIKE 'multi-turn-%';
DELETE FROM sessions WHERE id LIKE 'source-test-%';
```

Or reset the entire database:

```bash
docker compose down -v
docker compose up --build
```

## Troubleshooting

### Connection Refused

```
❌ Connection error! Make sure the API is running on http://localhost:8000
```

**Solution**: Start the API server:
```bash
docker compose up --build
```

### Test Failures

If tests fail, check:
1. API logs: `docker compose logs api`
2. Database connectivity: `docker compose ps`
3. Environment variables: `cat .env`
4. OpenAI API key validity
5. Custom API endpoint accessibility (if using OPENAI_API_BASE)

### Slow Tests

E2E tests may take 30-60 seconds total due to:
- Document indexing delays (2-3 seconds per document)
- LLM API calls (1-3 seconds per request)
- Vector similarity search

This is normal for E2E tests.

## CI/CD Integration

To integrate E2E tests into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    docker compose up -d
    sleep 10  # Wait for services to be ready
    python tests/e2e/run_all_e2e_tests.py
    docker compose down
```

## Production Readiness Criteria

The system is considered production-ready when:
- ✅ All 4 E2E test suites pass
- ✅ No errors in API logs
- ✅ Response times are acceptable (< 5s per request)
- ✅ Sources are accurately retrieved
- ✅ Context is preserved across turns
- ✅ Sessions are properly isolated

## Next Steps

After E2E tests pass:
1. Review Task 21 (Production deployment preparation)
2. Perform security review
3. Set up monitoring and alerting
4. Configure production environment
5. Deploy to production (Railway, AWS, etc.)
