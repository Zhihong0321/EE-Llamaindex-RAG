# Integration Tests

## Overview

This directory contains integration tests for the RAG API endpoints. The tests verify that all API endpoints work correctly with a real database and mocked OpenAI responses.

## Test Coverage

### Implemented Tests

1. **Health Endpoint Tests** (`test_health_endpoint.py`)
   - Tests GET /health endpoint accessibility
   - Verifies correct response structure (status, version)
   - Requirements: 1.1, 1.2, 1.3

2. **Ingest Endpoint Tests** (`test_ingest_endpoint.py`)
   - Tests POST /ingest endpoint with various payloads
   - Verifies document storage in database
   - Tests validation errors (missing fields, empty text)
   - Tests custom OpenAI API base URL configuration
   - Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 10.3

3. **Chat Endpoint Tests** (`test_chat_endpoint.py`)
   - Tests POST /chat endpoint functionality
   - Verifies session creation and management
   - Tests message storage (user and assistant messages)
   - Tests multi-turn conversations
   - Tests validation errors (missing fields)
   - Tests custom configuration parameters (top_k, temperature)
   - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 10.1, 10.2

4. **Documents Endpoint Tests** (`test_documents_endpoint.py`)
   - Tests GET /documents endpoint
   - Verifies document listing functionality
   - Tests correct field structure in responses
   - Requirements: 9.1, 9.2, 9.3

5. **Error Handling Tests** (`test_error_cases.py`)
   - Tests invalid JSON handling
   - Tests missing required fields
   - Tests invalid field types and values
   - Tests special characters and unicode
   - Tests SQL injection prevention
   - Tests concurrent requests
   - Requirements: 10.1, 10.2, 10.3, 10.4

## Known Issues

### LlamaIndex Circular Import

The current version of LlamaIndex (0.9.14) has a circular import issue that prevents direct import of services in test fixtures. This is a known issue with the library.

### Workarounds

There are two approaches to run these integration tests:

#### Option 1: Use the Running Application

The most reliable way to test the integration is to:

1. Start the application with Docker Compose:
   ```bash
   docker compose up --build
   ```

2. Run the existing `test_api.py` script which tests against the running application:
   ```bash
   python test_api.py
   ```

This approach tests the full integration including:
- Real database with pgvector
- Real LlamaIndex components
- Real OpenAI API calls (or custom API)
- All endpoints working together

#### Option 2: Fix LlamaIndex Version

Upgrade to a newer version of LlamaIndex that doesn't have the circular import issue:

```bash
pip install --upgrade llama-index
```

Then run the pytest integration tests:
```bash
pytest tests/integration/ -v
```

## Test Database Setup

The integration tests require a PostgreSQL database with pgvector extension. You can configure this in two ways:

1. **Set TEST_DB_URL environment variable** (recommended):
   ```bash
   export TEST_DB_URL="postgresql://user:pass@localhost:5432/test_db"
   ```

2. **Use existing DB_URL from .env**:
   The tests will use your configured database and create/drop tables per test.

## Running Tests

### All Integration Tests
```bash
pytest tests/integration/ -v
```

### Specific Test File
```bash
pytest tests/integration/test_health_endpoint.py -v
```

### Specific Test
```bash
pytest tests/integration/test_health_endpoint.py::test_health_endpoint_returns_ok -v
```

### With Coverage
```bash
pytest tests/integration/ --cov=app --cov-report=html
```

## Test Structure

Each test file follows this pattern:

1. **Setup**: Fixtures create test database, mock OpenAI components, and test client
2. **Test**: Execute API calls and verify responses
3. **Assertions**: Check status codes, response structure, and database state
4. **Cleanup**: Fixtures automatically clean up database tables

## Mocking Strategy

- **OpenAI Embedding Model**: Returns fixed embedding vectors
- **OpenAI LLM**: Returns predetermined responses
- **Vector Store**: Mocked to avoid actual vector operations
- **Database**: Real PostgreSQL with actual queries (integration testing)

## Future Improvements

1. Resolve LlamaIndex circular import issue
2. Add performance benchmarks
3. Add load testing scenarios
4. Add more edge case coverage
5. Add API rate limiting tests
