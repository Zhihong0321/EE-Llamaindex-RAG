````markdown
# Project Spec – LlamaIndex Conversational RAG API Server (MVP)

Owner: ME  
Target: Single backend service (Railway) exposing simple HTTP API for chat + ingestion  
Core engine: LlamaIndex (Python) + OpenAI API (embeddings + chat model)

---

## 1. Goals & Non-Goals

### 1.1 Goals (MVP)

- **G1 – RAG Chat API**  
  Provide a single `/chat` API endpoint that:
  - Accepts `session_id` + `message`.
  - Uses **LlamaIndex** to:
    - Retrieve relevant docs (vector search).
    - Combine with conversation history (memory).
    - Call OpenAI chat model.
  - Returns:
    - Final answer text.
    - Optional source list (doc IDs / titles).

- **G2 – Simple Ingestion API**  
  Provide a `/ingest` endpoint to push knowledge into the system:
  - Input: raw text or simple documents (for MVP, just text + optional metadata).
  - Automatically:
    - Chunk and embed via LlamaIndex.
    - Store in vector store.

- **G3 – Basic Memory**  
  For each `session_id`, store **chat history** in DB and feed recent turns to LlamaIndex’s chat engine so the bot feels “conversational”.

- **G4 – Easy to Deploy on Railway**  
  - Single service (container).
  - Connect to Railway Postgres.
  - Use environment variables for secrets (OpenAI key, DB URL).

### 1.2 Non-Goals (MVP)

- No file upload UI (only REST API).
- No multi-tenant ACLs or per-user doc permissions.
- No advanced long-term summarization (only store & replay recent messages).
- No streaming to frontend (MVP can be non-streaming; can extend later).

---

## 2. Tech Stack

### 2.1 Backend

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **LLM/RAG:** LlamaIndex
- **HTTP server:** Uvicorn / Gunicorn

### 2.2 AI Models (via OpenAI)

- **Embedding model:** `text-embedding-3-small`
- **Chat model:** `gpt-4.1-mini` (or equivalent, configurable via env)

> All model calls happen only inside the backend. Frontend never calls OpenAI directly.

### 2.3 Data Layer

- **DB:** PostgreSQL (Railway)
- **Vector store:** pgvector in same Postgres DB (via LlamaIndex integration)  
  > MVP assumption: Railway Postgres supports `pgvector` extension. If not, fallback to in-memory vector store for dev.

---

## 3. High-Level Architecture

1. **Client (frontend or other service)** calls backend:
   - `POST /chat` → send `session_id`, `message`.
   - `POST /ingest` → send `text` + metadata.

2. **API server (FastAPI)**
   - Validates request.
   - For `/chat`:
     - Loads recent messages from DB for that `session_id`.
     - Obtains LlamaIndex `chat_engine` (which uses the vector store).
     - Calls `chat_engine.chat(message)` with context.
     - Stores new user & assistant messages.
     - Returns response JSON.
   - For `/ingest`:
     - Wrap text in LlamaIndex `Document`.
     - Inserts into index (vector store).
     - Records metadata in DB.

3. **LlamaIndex Layer**
   - Embedding via OpenAI Embedding API.
   - Vector search via pgvector.
   - Chat engine using OpenAI Chat Completion API.

---

## 4. API Design (MVP)

### 4.1 Health Check

**Endpoint:** `GET /health`  
**Purpose:** For Railway & monitoring.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
````

---

### 4.2 Ingest Text

**Endpoint:** `POST /ingest`

**Request Body (JSON):**

```json
{
  "text": "Long brochure or documentation text here...",
  "title": "Eternalgy EMS Brochure",
  "source": "brochure_v1.pdf",
  "metadata": {
    "language": "en",
    "tags": ["ems", "brochure", "marketing"]
  }
}
```

**Backend behavior:**

1. Create LlamaIndex `Document` with:

   * `text`
   * `metadata` (including title, source, etc.).
2. Insert into index:

   * Chunk text.
   * Embed chunks.
   * Store in pgvector + DB.
3. Insert a row in DB `documents` table.

**Response:**

```json
{
  "document_id": "doc_123",
  "status": "indexed"
}
```

---

### 4.3 Chat

**Endpoint:** `POST /chat`

**Request Body (JSON):**

```json
{
  "session_id": "sess_abc123",
  "message": "Apa itu EMS Eternalgy?",
  "config": {
    "top_k": 5,
    "temperature": 0.3
  }
}
```

**Backend behavior:**

1. If `session_id` not exist:

   * Create new session row.

2. Load recent messages for `session_id`, limited by:

   * Last N turns (e.g. 10).
   * Or last M characters.

3. Build LlamaIndex `chat_engine`:

   * RAG mode (retriever + response synthesizer).
   * Provide conversation history as context (if supported), or manually construct system/user/assistant messages.

4. Call `chat_engine.chat(message)` (or equivalent).

5. Persist:

   * New user message.
   * Generated assistant reply.

6. Return answer + citations.

**Response:**

```json
{
  "session_id": "sess_abc123",
  "answer": "EMS Eternalgy ialah sistem pengurusan tenaga ...",
  "sources": [
    {
      "document_id": "doc_123",
      "title": "Eternalgy EMS Brochure",
      "snippet": "Eternalgy EMS helps factories monitor 30-minute MD blocks...",
      "score": 0.82
    }
  ]
}
```

---

### 4.4 (Optional) List Documents

**Endpoint:** `GET /documents`

**Response:**

```json
[
  {
    "document_id": "doc_123",
    "title": "Eternalgy EMS Brochure",
    "source": "brochure_v1.pdf",
    "created_at": "2025-11-14T05:00:00Z"
  }
]
```

---

## 5. Data Model (DB Schema)

### 5.1 `sessions` Table

Tracks conversation sessions.

```text
sessions (
  id              TEXT PRIMARY KEY,          -- session_id (e.g. 'sess_abc123')
  user_id         TEXT NULL,                 -- optional external user id
  created_at      TIMESTAMP WITH TIME ZONE,
  last_active_at  TIMESTAMP WITH TIME ZONE
)
```

### 5.2 `messages` Table

Stores chat history.

```text
messages (
  id              BIGSERIAL PRIMARY KEY,
  session_id      TEXT REFERENCES sessions(id) ON DELETE CASCADE,
  role            TEXT CHECK (role IN ('user', 'assistant', 'system')),
  content         TEXT,
  created_at      TIMESTAMP WITH TIME ZONE
)
```

### 5.3 `documents` Table

Tracks ingested documents (metadata only; vectors handled by LlamaIndex/pgvector).

```text
documents (
  id              TEXT PRIMARY KEY,          -- e.g. 'doc_123'
  title           TEXT,
  source          TEXT,                      -- filename, URL, or custom id
  metadata_json   JSONB,                     -- arbitrary metadata
  created_at      TIMESTAMP WITH TIME ZONE,
  updated_at      TIMESTAMP WITH TIME ZONE
)
```

### 5.4 `pgvector` integration

* LlamaIndex will create/use extra tables to store vectors (depending on adapter).
* Ensure `CREATE EXTENSION IF NOT EXISTS vector;` on DB.

---

## 6. LlamaIndex Layer (Design)

### 6.1 Initialization

On app startup:

1. Configure embedding model:

   ```python
   from llama_index.embeddings.openai import OpenAIEmbedding
   embed_model = OpenAIEmbedding(model="text-embedding-3-small")
   ```

2. Configure OpenAI LLM:

   ```python
   from llama_index.llms.openai import OpenAI
   llm = OpenAI(model="gpt-4.1-mini", temperature=0.3)
   ```

3. Configure vector store (pgvector via LlamaIndex PGVector integration).

4. Create / load `index` from DB, and a `chat_engine` factory, e.g.:

   * `index = VectorStoreIndex.from_vector_store(...)`
   * `chat_engine = index.as_chat_engine(...)`

> Exact code is for Codex to generate. Spec only defines intent.

### 6.2 Chat Flow with Memory

For each `/chat` call:

1. Load last N messages from `messages` table.
2. Build context prompt:

   * System message: high-level instructions (persona, language).
   * Append recent user/assistant messages.
3. Provide this into LlamaIndex chat engine (either via memory object or manual context injection).
4. Retrieve relevant document chunks via `top_k`.
5. Generate final answer from LLM.

---

## 7. Configuration & Environment Variables

Define environment variables:

```text
OPENAI_API_KEY         = "sk-..."
DB_URL                 = "postgresql://user:pass@host:port/dbname"
EMBEDDING_MODEL        = "text-embedding-3-small"
CHAT_MODEL             = "gpt-4.1-mini"
MAX_HISTORY_MESSAGES   = 10        # or similar
TOP_K_DEFAULT          = 5
```

On Railway, set all environment variables in the service settings.

---

## 8. Deployment Notes (Railway)

1. **Prepare Postgres**:

   * Create Railway Postgres instance.
   * Run migrations to create `sessions`, `messages`, `documents`, and enable `pgvector`.

2. **Backend service**:

   * Connect GitHub repo.
   * `Dockerfile` / `build` using Poetry or pip.
   * Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

3. **Volumes** (optional):

   * For caching or local index storage if needed (MVP can rely fully on DB).

---

## 9. MVP Milestones / Checkpoints

### M1 – Skeleton API (no LlamaIndex yet)

* FastAPI project structure created.
* `/health` endpoint returns `ok`.
* Postgres connection works.
* `/chat` returns dummy echo response.

**Checkpoint:** Call `/chat` from Postman and receive echo.

---

### M2 – DB & Sessions

* `sessions` and `messages` tables created.
* `/chat`:

  * Creates new session if needed.
  * Stores messages (role + content) in DB.
  * Still returns dummy answer.

**Checkpoint:** Verify DB rows for sessions and messages.

---

### M3 – LlamaIndex + Ingestion

* LlamaIndex configured with:

  * OpenAI embeddings.
  * pgvector vector store.
* `/ingest`:

  * Creates `Document` and indexes it.
  * Inserts row into `documents` table.

**Checkpoint:** Ingest some sample text and confirm vectors exist (via logs or DB).

---

### M4 – RAG Chat

* `/chat`:

  * Uses LlamaIndex chat engine.
  * Performs vector retrieval from ingested docs.
  * Includes recent chat history in context.
  * Returns `answer` + `sources`.

**Checkpoint:** Ask question about ingested text and get accurate answer + source metadata.

---

### M5 – Hardening (Optional)

* Error handling & logging.
* Config via env vars.
* Simple rate limiting or auth stub (API key header).

---

*End of Spec*

