# LlamaIndex RAG API

A conversational RAG (Retrieval-Augmented Generation) API server built with LlamaIndex and FastAPI. This system enables document ingestion, vector-based retrieval, and context-aware conversations with an AI assistant.

## Features

- **Document Ingestion**: Upload and index text documents for retrieval
- **Conversational Chat**: Context-aware conversations with chat history
- **Vector Search**: Semantic search using OpenAI embeddings and pgvector
- **Session Management**: Multi-session support with conversation isolation
- **Source Attribution**: Responses include source documents with relevance scores

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd llamaindex-rag-api
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL with pgvector

Install PostgreSQL and the pgvector extension:

```bash
# On Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-14-pgvector

# On macOS with Homebrew
brew install postgresql@14
brew install pgvector
```

Create a database:

```bash
createdb llamaindex_rag
psql llamaindex_rag -c "CREATE EXTENSION vector;"
```

### 5. Configure environment variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DB_URL`: Your PostgreSQL connection string

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```
GET /health
```

### Ingest Document
```
POST /ingest
Content-Type: application/json

{
  "text": "Your document text here",
  "title": "Document Title (optional)",
  "source": "Source URL or identifier (optional)",
  "metadata": {}
}
```

### Chat
```
POST /chat
Content-Type: application/json

{
  "session_id": "unique-session-id",
  "message": "Your question here",
  "config": {
    "top_k": 5,
    "temperature": 0.3
  }
}
```

### List Documents (Optional)
```
GET /documents
```

## Configuration

All configuration is done via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DB_URL` | PostgreSQL connection string | Required |
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` |
| `CHAT_MODEL` | OpenAI chat model | `gpt-4o-mini` |
| `MAX_HISTORY_MESSAGES` | Max messages in chat history | `10` |
| `TOP_K_DEFAULT` | Default number of retrieved chunks | `5` |
| `DEFAULT_TEMPERATURE` | Default LLM temperature | `0.3` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `VERSION` | API version | `0.1.0` |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run with coverage
pytest --cov=app tests/
```

### Code Structure

```
llamaindex-rag-api/
├── app/
│   ├── api/          # API endpoints
│   ├── services/     # Business logic
│   ├── models/       # Pydantic models
│   ├── db/           # Database connection
│   ├── llama/        # LlamaIndex setup
│   ├── config.py     # Configuration
│   └── main.py       # FastAPI app
├── alembic/          # Database migrations
├── tests/            # Test suites
└── requirements.txt  # Dependencies
```

## Deployment

### Production Deployment

For comprehensive production deployment instructions, see:
- **[Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)** - Complete deployment instructions for Railway and other platforms
- **[Security Checklist](SECURITY_CHECKLIST.md)** - Security review and hardening guide
- **[Performance Optimization](PERFORMANCE_OPTIMIZATION.md)** - Performance tuning and optimization strategies
- **[Monitoring Guide](MONITORING_GUIDE.md)** - Monitoring, alerting, and observability setup

### Quick Start: Railway Deployment

Railway provides the simplest deployment experience with managed PostgreSQL and automatic deployments.

#### Prerequisites
- Railway account ([sign up here](https://railway.app))
- OpenAI API key
- GitHub repository (for automatic deployments)

#### Deployment Steps

1. **Create Railway Project**
   - Go to [Railway](https://railway.app) and create a new project
   - Select "Deploy from GitHub repo" and connect your repository

2. **Add PostgreSQL Database**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway automatically provisions PostgreSQL with pgvector support

3. **Configure Environment Variables**
   ```bash
   # Required
   OPENAI_API_KEY=sk-...
   DB_URL=${{Postgres.DATABASE_URL}}  # Auto-injected by Railway
   
   # Production Settings
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   WORKERS=2
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Deploy**
   - Railway auto-detects the Dockerfile and deploys
   - Migrations run automatically on startup
   - Access your API at the provided Railway URL

5. **Verify Deployment**
   ```bash
   # Check health
   curl https://your-app.railway.app/health
   
   # View API docs
   open https://your-app.railway.app/docs
   ```

#### Production Configuration

For production deployments, ensure you:
- ✅ Set `ENVIRONMENT=production`
- ✅ Configure specific CORS origins (not `*`)
- ✅ Set appropriate `LOG_LEVEL` (INFO or WARNING)
- ✅ Configure `WORKERS` based on CPU cores (2-4 recommended)
- ✅ Enable monitoring and alerting
- ✅ Review the [Security Checklist](SECURITY_CHECKLIST.md)

See [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) for detailed instructions.

### Docker

Build and run with Docker:

```bash
# Build the image
docker build -t llamaindex-rag-api .

# Run with environment file
docker run -p 8000:8000 --env-file .env llamaindex-rag-api

# Or run with individual environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e DB_URL=postgresql://user:pass@host:5432/db \
  llamaindex-rag-api
```

#### Docker Compose

For local development with PostgreSQL:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: llamaindex_rag
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DB_URL: postgresql://postgres:postgres@postgres:5432/llamaindex_rag
    depends_on:
      - postgres

volumes:
  postgres_data:
```

Run with: `docker-compose up`

## Troubleshooting

### pgvector extension not found
Ensure pgvector is installed and enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### OpenAI API errors
- Verify your API key is correct
- Check your OpenAI account has sufficient credits
- Ensure you have access to the specified models

### Database connection issues
- Verify PostgreSQL is running
- Check the DB_URL format: `postgresql://user:password@host:port/database`
- Ensure the database exists and is accessible

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
