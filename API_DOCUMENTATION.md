# API Documentation for Frontend Team

## 🚀 Quick Access

Your RAG API automatically exposes interactive API documentation at:

- **Swagger UI (Interactive)**: `http://your-domain/docs`
- **ReDoc (Alternative)**: `http://your-domain/redoc`
- **OpenAPI JSON Schema**: `http://your-domain/openapi.json`

## 📍 Base URL

- **Production**: `https://your-production-url.railway.app`
- **Local Development**: `http://localhost:8000`

## 🔑 Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## 📡 Available Endpoints

### 1. Health Check
```
GET /health
```
Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T10:30:00Z"
}
```

---

### 2. Vault Management

#### 2.1 Create Vault
```
POST /vaults
```
Create a new vault for organizing documents.

**Request Body:**
```json
{
  "name": "My Vault",
  "description": "Optional description"
}
```

**Response (201 Created):**
```json
{
  "vault_id": "uuid-here",
  "name": "My Vault",
  "description": "Optional description",
  "created_at": "2025-11-21T10:30:00Z",
  "document_count": 0
}
```

**Error Responses:**
- `409 Conflict`: Vault with same name already exists
- `422 Unprocessable Entity`: Invalid request (missing name)

---

#### 2.2 List All Vaults
```
GET /vaults
```
Retrieve all vaults with document counts.

**Response (200 OK):**
```json
[
  {
    "vault_id": "uuid-1",
    "name": "Vault 1",
    "description": "First vault",
    "created_at": "2025-11-21T10:30:00Z",
    "document_count": 5
  },
  {
    "vault_id": "uuid-2",
    "name": "Vault 2",
    "description": "Second vault",
    "created_at": "2025-11-21T11:00:00Z",
    "document_count": 3
  }
]
```

---

#### 2.3 Get Single Vault
```
GET /vaults/{vault_id}
```
Retrieve a specific vault by ID.

**Response (200 OK):**
```json
{
  "vault_id": "uuid-here",
  "name": "My Vault",
  "description": "Optional description",
  "created_at": "2025-11-21T10:30:00Z",
  "document_count": 5
}
```

**Error Responses:**
- `404 Not Found`: Vault does not exist

---

#### 2.4 Delete Vault
```
DELETE /vaults/{vault_id}
```
Delete a vault and all its associated documents (cascade delete).

**Response (200 OK):**
```json
{
  "vault_id": "uuid-here",
  "status": "deleted"
}
```

**Error Responses:**
- `404 Not Found`: Vault does not exist

---

### 3. Document Ingestion
```
POST /ingest
```
Upload and process documents for RAG retrieval.

**Request Body:**
```json
{
  "text": "Your document content here...",
  "title": "Document Title",
  "source": "source.pdf",
  "vault_id": "optional-vault-uuid",
  "metadata": {
    "author": "John Doe"
  }
}
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "status": "indexed"
}
```

**Notes:**
- `vault_id` is optional. If provided, the vault must exist (returns 404 if not).
- Documents are automatically chunked and embedded.

---

### 4. Chat (Query)
```
POST /chat
```
Send a message and get an AI-generated response based on ingested documents.

**Request Body:**
```json
{
  "session_id": "session-uuid",
  "message": "What is the main topic of the documents?",
  "vault_id": "optional-vault-uuid",
  "config": {
    "top_k": 5,
    "temperature": 0.3
  }
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "answer": "Based on the documents, the main topic is...",
  "sources": [
    {
      "document_id": "doc-uuid",
      "title": "Document Title",
      "snippet": "Relevant excerpt...",
      "score": 0.95
    }
  ]
}
```

**Notes:**
- `vault_id` is optional. If provided, only documents in that vault are used for context.
- `config` is optional with defaults: `top_k=5`, `temperature=0.3`
  "message_id": "msg-uuid"
}
```

**Streaming Response:**
When `stream: true`, the response is sent as Server-Sent Events (SSE):
```
Content-Type: text/event-stream

data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "token", "content": " the"}
data: {"type": "sources", "sources": [...]}
data: {"type": "done"}
```

---

### 4. List Documents
```
GET /documents?limit=10&offset=0
```
Retrieve a list of all ingested documents.

**Query Parameters:**
- `limit` (optional): Number of documents to return (default: 10)
- `offset` (optional): Number of documents to skip (default: 0)

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid-here",
      "metadata": {
        "title": "Document Title",
        "source": "source.pdf"
      },
      "created_at": "2025-11-17T10:00:00Z",
      "chunk_count": 5
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

---

### 5. Get Document by ID
```
GET /documents/{document_id}
```
Retrieve details of a specific document.

**Response:**
```json
{
  "id": "uuid-here",
  "content": "Full document content...",
  "metadata": {
    "title": "Document Title",
    "source": "source.pdf"
  },
  "created_at": "2025-11-17T10:00:00Z",
  "chunks": [
    {
      "id": "chunk-uuid",
      "content": "Chunk content...",
      "embedding_id": "embedding-uuid"
    }
  ]
}
```

---

### 6. Delete Document
```
DELETE /documents/{document_id}
```
Delete a document and all its associated chunks.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "uuid-here"
}
```

---

## 🔄 Session Management

The chat endpoint supports multi-turn conversations through sessions:

1. **First message**: Omit `session_id` or send `null`. The API creates a new session.
2. **Follow-up messages**: Include the `session_id` from the previous response to continue the conversation.

**Example Flow:**
```javascript
// First message
const response1 = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({ message: "Hello" })
});
const { session_id } = await response1.json();

// Follow-up message
const response2 = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({ 
    message: "Tell me more",
    session_id: session_id 
  })
});
```

---

## 🌊 Streaming Responses

For real-time chat responses, use `stream: true`:

```javascript
const response = await fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Your question",
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      if (data.type === 'token') {
        console.log(data.content); // Display token
      } else if (data.type === 'sources') {
        console.log(data.sources); // Display sources
      } else if (data.type === 'done') {
        console.log('Stream complete');
      }
    }
  }
}
```

---

## ⚠️ Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes:

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request parameters |
| 404 | `SESSION_NOT_FOUND` | Session ID doesn't exist |
| 404 | `DOCUMENT_NOT_FOUND` | Document ID doesn't exist |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 500 | `DOCUMENT_INGEST_ERROR` | Failed to ingest document |
| 500 | `CHAT_GENERATION_ERROR` | Failed to generate response |
| 500 | `MESSAGE_SAVE_ERROR` | Failed to save message |
| 502 | `OPENAI_ERROR` | OpenAI API error |
| 503 | `DATABASE_ERROR` | Database connection error |

---

## 🔧 CORS Configuration

The API is configured with permissive CORS settings:

- **Allowed Origins**: `*` (all origins)
- **Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- **Allowed Headers**: `*` (all headers)
- **Credentials**: Supported
- **Max Age**: 3600 seconds (1 hour)

---

## 📦 TypeScript Types

Here are TypeScript interfaces for the API:

```typescript
// Request Types
interface IngestRequest {
  content: string;
  metadata?: Record<string, any>;
}

interface ChatRequest {
  message: string;
  session_id?: string | null;
  stream?: boolean;
}

// Response Types
interface HealthResponse {
  status: string;
  timestamp: string;
}

interface IngestResponse {
  document_id: string;
  status: string;
  chunks_created: number;
  metadata: Record<string, any>;
}

interface Source {
  document_id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
}

interface ChatResponse {
  response: string;
  session_id: string;
  sources: Source[];
  message_id: string;
}

interface StreamEvent {
  type: 'token' | 'sources' | 'done';
  content?: string;
  sources?: Source[];
}

interface Document {
  id: string;
  metadata: Record<string, any>;
  created_at: string;
  chunk_count?: number;
  content?: string;
  chunks?: Array<{
    id: string;
    content: string;
    embedding_id: string;
  }>;
}

interface DocumentsListResponse {
  documents: Document[];
  total: number;
  limit: number;
  offset: number;
}

interface ErrorResponse {
  error: string;
  detail: string;
  code: string;
}
```

---

## 🧪 Testing the API

### Using cURL:

```bash
# Health check
curl http://localhost:8000/health

# Ingest document
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Test document", "metadata": {"title": "Test"}}'

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this about?"}'

# List documents
curl http://localhost:8000/documents?limit=5
```

### Using JavaScript/Fetch:

```javascript
// Ingest document
const ingestDoc = async () => {
  const response = await fetch('http://localhost:8000/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: 'Your document content',
      metadata: { title: 'My Document' }
    })
  });
  return await response.json();
};

// Chat
const chat = async (message, sessionId = null) => {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      stream: false
    })
  });
  return await response.json();
};
```

---

## 📚 Additional Resources

- **Interactive API Docs**: Visit `/docs` for Swagger UI with live testing
- **Alternative Docs**: Visit `/redoc` for ReDoc documentation
- **OpenAPI Schema**: Download from `/openapi.json` for code generation

---

## 🆘 Support

For issues or questions:
1. Check the interactive docs at `/docs`
2. Review error codes and messages
3. Check server logs for detailed error information
4. Contact the backend team

---

**Last Updated**: November 17, 2025
**API Version**: 0.1.0


---

### 3. Agent Management

#### 3.1 Create Agent
```
POST /agents
```
Create a new AI agent configuration associated with a vault.

**Request Body:**
```json
{
  "name": "Customer Support Agent",
  "vault_id": "uuid-of-vault",
  "system_prompt": "You are a helpful customer support agent. Be polite and professional."
}
```

**Response (200 OK):**
```json
{
  "agent_id": "uuid-here",
  "name": "Customer Support Agent",
  "vault_id": "uuid-of-vault",
  "system_prompt": "You are a helpful customer support agent. Be polite and professional.",
  "created_at": "2025-11-29T10:30:00Z"
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Invalid request (missing required fields)
- `500 Internal Server Error`: Failed to create agent

---

#### 3.2 List All Agents
```
GET /agents
```
Retrieve all agents, optionally filtered by vault.

**Query Parameters:**
- `vault_id` (optional): Filter agents by vault ID

**Examples:**
```
GET /agents                          # Get all agents
GET /agents?vault_id=uuid-of-vault   # Get agents for specific vault
```

**Response (200 OK):**
```json
[
  {
    "agent_id": "uuid-1",
    "name": "Customer Support Agent",
    "vault_id": "uuid-of-vault",
    "system_prompt": "You are a helpful customer support agent...",
    "created_at": "2025-11-29T10:30:00Z"
  },
  {
    "agent_id": "uuid-2",
    "name": "Technical Support Agent",
    "vault_id": "uuid-of-vault",
    "system_prompt": "You are a technical support specialist...",
    "created_at": "2025-11-29T11:00:00Z"
  }
]
```

---

#### 3.3 Get Single Agent
```
GET /agents/{agent_id}
```
Retrieve a specific agent by ID.

**Response (200 OK):**
```json
{
  "agent_id": "uuid-here",
  "name": "Customer Support Agent",
  "vault_id": "uuid-of-vault",
  "system_prompt": "You are a helpful customer support agent. Be polite and professional.",
  "created_at": "2025-11-29T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Agent does not exist

---

#### 3.4 Delete Agent
```
DELETE /agents/{agent_id}
```
Delete an agent configuration.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Agent deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Agent does not exist
- `500 Internal Server Error`: Failed to delete agent

---

## 🔄 Agent Workflow Example

Here's a typical workflow for using agents:

```javascript
// 1. Create a vault
const vault = await fetch('http://localhost:8000/vaults', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Customer Support KB',
    description: 'Knowledge base for customer support'
  })
}).then(r => r.json());

// 2. Ingest documents into the vault
await fetch('http://localhost:8000/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Product documentation content...',
    title: 'Product Guide',
    vault_id: vault.vault_id
  })
});

// 3. Create an agent for this vault
const agent = await fetch('http://localhost:8000/agents', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Support Bot',
    vault_id: vault.vault_id,
    system_prompt: 'You are a helpful support agent. Use the knowledge base to answer questions.'
  })
}).then(r => r.json());

// 4. Use the agent in chat (with vault filtering)
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'user-session-123',
    message: 'How do I reset my password?',
    vault_id: vault.vault_id  // Filter to only this vault's documents
  })
}).then(r => r.json());

console.log(response.answer);
```

---

## 📝 Notes for Frontend Team

### Agent Management
- **Agents are tied to vaults**: Each agent must be associated with a vault
- **Cascade deletion**: When a vault is deleted, all its agents are automatically deleted
- **System prompts**: Define the agent's personality and behavior
- **Filtering**: Use `vault_id` query parameter to get agents for a specific vault
- **No authentication**: Currently no auth required (add if needed)

### Best Practices
1. **Create vaults first**: Always create a vault before creating agents
2. **Meaningful names**: Use descriptive names for agents (e.g., "Customer Support Bot", "Technical Assistant")
3. **Clear prompts**: Write clear system prompts that define the agent's role and behavior
4. **Error handling**: Always handle 404 errors when fetching/deleting agents
5. **Validation**: Frontend should validate that vault_id exists before creating an agent

### Testing
Use the provided test script to verify the implementation:
```bash
python test_agents_api.py
```

---

## 🐛 Troubleshooting

### Agent Creation Fails
- **Check vault exists**: Ensure the `vault_id` references an existing vault
- **Validate fields**: All fields (name, vault_id, system_prompt) are required
- **Check logs**: Server logs will show detailed error messages

### Agent Not Found (404)
- **Verify agent_id**: Ensure you're using the correct UUID
- **Check deletion**: Agent may have been deleted or vault was deleted (cascade)

### Empty Agent List
- **Check vault_id**: If filtering by vault, ensure the vault has agents
- **Verify creation**: Ensure agents were successfully created

---
