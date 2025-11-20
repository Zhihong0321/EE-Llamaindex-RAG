# Front‑End Specification & Development Guide for EE‑LlamaIndex RAG API

## 1️⃣ High‑Level Architecture
```
┌─────────────────────┐          ┌─────────────────────┐
│   Front‑End (SPA)   │  HTTPS   │   FastAPI Backend   │
│  React / Vite /     │◀──────▶  │  (Python, LlamaIndex)│
│  Next.js            │          │  ├─ /ingest          │
│                     │          │  ├─ /documents       │
│                     │          │  ├─ /chat            │
│                     │          │  ├─ /vaults*         │   ← new
│                     │          │  ├─ /agents*         ← new
│                     │          │  └─ /ingest‑status* ← new
└─────────────────────┘          └─────────────────────┘
```
*`*` = endpoints that are **planned** but not yet in the repo. The spec includes them so the UI can be built now.

---

## 2️⃣ API ENDPOINT CATALOG
| Method | Path | Purpose | Request Body | Response | Notes |
|--------|------|---------|--------------|----------|-------|
| **POST** | `/vaults` | Create a new Vault (knowledge base) | `VaultCreateRequest` | `VaultResponse` (id, name, description, created_at) | Returns a UUID `vault_id`. |
| **GET** | `/vaults` | List all Vaults | – | `VaultListResponse` (array of vault objects) | |
| **GET** | `/vaults/{vault_id}` | Get details of a Vault | – | `VaultResponse` | |
| **DELETE** | `/vaults/{vault_id}` | Delete a Vault (cascades to docs & agents) | – | `DeleteResponse` | |
| **POST** | `/ingest` | Upload a document (text) to a Vault | `IngestRequest` (see below) | `IngestResponse` (document_id, task_id) | Returns a **task_id** for progress tracking. |
| **GET** | `/ingest/status/{task_id}` | Poll ingestion progress | – | `IngestStatusResponse` (status: `queued|processing|done|failed`, progress 0‑100, error?) | New endpoint. |
| **GET** | `/documents` | List documents (optionally filter by Vault) | Query param `vault_id` (optional) | `DocumentsResponse` | |
| **DELETE** | `/documents/{document_id}` | Delete a document (removes from vector store & DB) | – | `DeleteResponse` | |
| **POST** | `/agents` | Create a new Agent (name + Vault + system prompt) | `AgentCreateRequest` | `AgentResponse` (agent_id, name, vault_id, system_prompt, created_at) | |
| **GET** | `/agents` | List all Agents (filter by Vault) | Query param `vault_id` (optional) | `AgentListResponse` | |
| **GET** | `/agents/{agent_id}` | Get Agent details | – | `AgentResponse` | |
| **DELETE** | `/agents/{agent_id}` | Delete an Agent | – | `DeleteResponse` | |
| **POST** | `/chat` | Chat with an Agent (or directly with a Vault) | `ChatRequest` (includes `vault_id` **or** `agent_id`) | `ChatResponse` (answer, sources, session_id) | Existing endpoint – we will extend the request model to accept `agent_id`. |

### 2.1 Request / Response Schemas (Pydantic)
#### VaultCreateRequest
```json
{ "name": "HR Knowledge Base", "description": "All HR policies, handbooks, FAQs" }
```
#### VaultResponse
```json
{ "id": "c0a1e5b2-8f4d-4a9c-9b2e-7d5f9a3e9c1f", "name": "HR Knowledge Base", "description": "All HR policies, handbooks, FAQs", "created_at": "2025-11-20T12:00:00Z" }
```
#### IngestRequest *(updated)*
```json
{ "text": "Full plain‑text of the document", "title": "Employee Handbook", "source": "handbook.pdf", "vault_id": "c0a1e5b2-8f4d-4a9c-9b2e-7d5f9a3e9c1f", "metadata": { "author": "HR Dept.", "tags": ["policy","benefits"] } }
```
#### IngestResponse
```json
{ "document_id": "d5f9c2e1-7b3a-4c9d-8e2f-9a6b5c7d8e9f", "task_id": "ingest-20251120-001" }
```
#### IngestStatusResponse
```json
{ "task_id": "ingest-20251120-001", "status": "processing", "progress": 57, "error": null }
```
#### AgentCreateRequest
```json
{ "name": "HR Assistant", "vault_id": "c0a1e5b2-8f4d-4a9c-9b2e-7d5f9a3e9c1f", "system_prompt": "You are a helpful HR assistant. Answer politely and cite sources." }
```
#### AgentResponse
```json
{ "agent_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab", "name": "HR Assistant", "vault_id": "c0a1e5b2-8f4d-4a9c-9b2e-7d5f9a3e9c1f", "system_prompt": "You are a helpful HR assistant...", "created_at": "2025-11-20T12:45:00Z" }
```
#### ChatRequest *(extended)*
```json
{ "session_id": "sess-001", "message": "What is the vacation policy?", "vault_id": "c0a1e5b2-8f4d-4a9c-9b2e-7d5f9a3e9c1f", "agent_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab", "config": { "top_k": 5, "temperature": 0.3 } }
```
#### ChatResponse (unchanged)
```json
{ "session_id": "sess-001", "answer": "Employees receive 20 days of paid vacation per year.", "sources": [ { "document_id": "d5f9c2e1-...", "title": "Employee Handbook", "snippet": "Vacation accrual is 1.66 days per month...", "score": 0.92 } ] }
```
---

## 3️⃣ UI COMPONENT SPECIFICATION
| Page | Core Components | Description |
|------|----------------|-------------|
| **Dashboard** | `VaultSelector`, `AgentCardList`, `RecentIngests`, `QuickChatBox` | Overview of all Vaults, Agents, and latest ingestion jobs. |
| **Vault Management** | `VaultList`, `VaultFormModal`, `VaultDeleteConfirm` | Create, edit, delete vaults. |
| **Document Upload** | `DocumentUploadForm`, `IngestProgressBar`, `DocumentTable` | Drag‑&‑drop → POST `/ingest` → poll `/ingest/status/{task_id}`. |
| **Agent Management** | `AgentList`, `AgentFormModal`, `AgentDeleteConfirm`, `AgentCURLSnippet` | Create agents bound to a vault, edit system prompt, view ready‑made cURL. |
| **Chat Console** | `ChatWindow`, `ChatMessageBubble`, `ChatInput`, `ChatSourceList` | Interactive chat UI that sends `ChatRequest` (with `agent_id` or `vault_id`). |
| **cURL Helper** | `CurlSnippetModal` (re‑usable) | Generates a copy‑ready cURL command for any endpoint. |

### 3.1 `VaultSelector`
* **Props:** `vaults: Vault[]`, `selectedVaultId: string`, `onSelect(vaultId)`
* **UI:** Dropdown with glass‑morphism background.

### 3.2 `DocumentUploadForm`
* File picker (`accept=".pdf,.docx,.txt,.md"`).
* Optional metadata fields (title, source, extra JSON).
* **Vault selector** (required).
* **Submit** → POST `/ingest`. After submit show `IngestProgressBar` that polls `/ingest/status/{task_id}` every 2 s.

### 3.3 `IngestProgressBar`
* **Props:** `taskId`, `onComplete(callback)`.
* Linear progress bar (0‑100 %). When `status === "done"` → fire `onComplete`.

### 3.4 `AgentFormModal`
* Fields: Agent name, Vault selector, System prompt (textarea).
* **Submit:** POST `/agents`. Returns `agent_id`.

### 3.5 `AgentCURLSnippet`
```bash
curl -X POST https://<host>/chat \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "sess-$(uuidgen)",
        "agent_id": "<AGENT_ID>",
        "message": "Your question here",
        "config": {"top_k":5,"temperature":0.3}
      }'
```
* Copy button → copies to clipboard, shows toast.

---

## 4️⃣ Interaction Flow Diagrams
### 4.1 Document Ingestion Flow
```
User → selects Vault → uploads file → clicks “Ingest”
   │
   ▼
POST /ingest (payload includes vault_id)
   │
   ▼
Backend returns {document_id, task_id}
   │
   ▼
UI starts polling GET /ingest/status/{task_id}
   │
   ├─► status = processing → update progress bar
   └─► status = done → show success toast, refresh DocumentTable
```
### 4.2 Agent Creation & Usage Flow
```
User → “Create Agent” → fills name, selects Vault, writes system prompt
   │
   ▼
POST /agents
   │
   ▼
Backend returns {agent_id}
   │
   ▼
Agent list updates → user clicks “Copy cURL” → cURL snippet generated (includes agent_id)
   │
   ▼
User can run the snippet in terminal or use UI Chat console:
   → POST /chat (agent_id + message)
   → UI displays answer + source cards
```
---

## 5️⃣ Example cURL Snippets (Ready‑to‑Copy)
| Action | cURL |
|--------|------|
| **Create Vault** | ```bash
curl -X POST https://api.example.com/vaults \
  -H "Content-Type: application/json" \
  -d '{"name":"HR Knowledge Base","description":"All HR policies"}'
``` |
| **Upload Document** | ```bash
curl -X POST https://api.example.com/ingest \
  -H "Content-Type: application/json" \
  -d '{"text":"$(cat handbook.txt)","title":"Employee Handbook","source":"handbook.pdf","vault_id":"<VAULT_ID>"}'
``` |
| **Poll Ingestion** | ```bash
curl https://api.example.com/ingest/status/<TASK_ID>
``` |
| **Create Agent** | ```bash
curl -X POST https://api.example.com/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"HR Assistant","vault_id":"<VAULT_ID>","system_prompt":"You are a helpful HR assistant."}'
``` |
| **Chat with Agent** | ```bash
curl -X POST https://api.example.com/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"sess-$(uuidgen)","agent_id":"<AGENT_ID>","message":"What is the vacation policy?"}'
``` |
| **List Documents (filter by Vault)** | ```bash
curl https://api.example.com/documents?vault_id=<VAULT_ID>
``` |
---

## 6️⃣ Development Guidelines for the Front‑End Team
| Area | Recommendation |
|------|----------------|
| **Project Scaffold** | `npx -y create-vite@latest ./frontend --template react-ts` (or `next` if you need server‑side rendering). |
| **Styling** | Vanilla CSS with **CSS Modules** or **styled‑components**. Avoid Tailwind unless the team explicitly wants it. |
| **Design System** | Create a `src/theme.ts` exporting colors, fonts, spacing tokens. Use them everywhere for a consistent premium look. |
| **API Client** | Wrap `fetch` in a tiny `api.ts` that automatically adds `Content-Type: application/json` and handles JSON parsing + error mapping. |
| **Testing** | Use **Vitest** (or Jest) for unit tests, **Playwright** for end‑to‑end UI tests (e.g., upload → progress → success). |
| **CI/CD** | Lint with **ESLint** (airbnb‑base + prettier). Run `npm run lint && npm run test` on PRs. |
| **Documentation** | Add a `README.md` in the `frontend/` folder that lists: `npm install`, `npm run dev`, `npm run build`, and how to set the API base URL (`.env` variable `VITE_API_BASE`). |
| **Versioning** | Keep the UI version in `package.json` synced with the backend tag (e.g., `v1.3.0‑vault‑agent`). |
| **Accessibility** | Use `role="alert"` for toast messages, `aria-live="polite"` for progress updates. |
| **Performance** | Lazy‑load the **Chat** page, memoize heavy components (`React.memo`). Keep the bundle < 2 MB (gzip). |

---

## 7️⃣ “Next Steps” for Backend (to make UI functional)
1. **Add the new endpoints** (`/vaults`, `/agents`, `/ingest/status/{task_id}`) – simple CRUD wrappers around PostgreSQL tables. 
2. **Expose `agent_id` in the `ChatRequest` model** (already added in the spec). 
3. **Return a `task_id` from `/ingest`** and store ingestion progress in a lightweight table (`ingest_tasks`) so the UI can poll. 
4. **Update OpenAPI** – once the new routes are added, the Swagger UI (`/docs`) will instantly reflect them. 

---

### 🎉 That’s the complete front‑end spec! Save this file as `llamaIndex_frontend.md` and share it with the UI developers. They can now build a premium‑looking SPA that creates vaults, uploads documents, monitors ingestion, creates agents, chats, and even copies ready‑made cURL commands.
