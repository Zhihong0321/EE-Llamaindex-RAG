# RAG Management Workflow & Architecture

This document outlines the complete workflow for managing multiple Knowledge Vaults (Tenants) and their associated data, as well as how to structure the API for the Frontend team.

## 1. The Core Concept: "Vaults" & "Agents"

To support your requirement, we introduce two key concepts:
*   **Vault (Knowledge Base):** A secure container for documents. (e.g., "HR Docs", "Technical Manuals", "Client X Project").
*   **Agent (The Brain):** A configured personality that "talks" to a specific Vault.

---

## 2. Workflow: Vault & Knowledge Management

### Step 1: Vault Setup (Configuration)
Before ingesting files, you define a "Vault". This is logical grouping.
*   **Action:** Create a unique ID for the vault (e.g., `vault_hr_01`).
*   **Frontend UI:** A "Create New Knowledge Base" button.
*   **API:** No specific "create vault" endpoint is strictly needed *if* you just use metadata tags, BUT for a robust system, you might want a `POST /vaults` to store vault settings (name, description).

### Step 2: Content Management (CRUD)
This is the cycle for populating the vault.

**A. Ingest (Upload)**
*   **User Action:** Uploads "Employee_Handbook.pdf" to "HR Vault".
*   **API Call:**
    ```http
    POST /ingest
    {
      "text": "...extracted text...",
      "metadata": {
        "vault_id": "vault_hr_01",  <-- CRITICAL: Links doc to vault
        "filename": "Employee_Handbook.pdf"
      }
    }
    ```

**B. List (View)**
*   **User Action:** Views files in "HR Vault".
*   **API Call:**
    ```http
    GET /documents?vault_id=vault_hr_01
    ```
    *Result:* Only shows files belonging to that vault.

**C. Delete (Remove)**
*   **User Action:** Deletes "Old_Policy.pdf".
*   **API Call:**
    ```http
    DELETE /documents/{document_id}
    ```
    *Result:* Removes it from the Vector Store and Database.

---

## 3. Chat & Agent Workflow

### Step 3: Chatting with a Vault
You asked: *"Does the current chat completion api, can select which vault it use?"*
*   **Currently:** No, it searches *everything*.
*   **Required Change:** We must update the `/chat` endpoint to accept a `vault_id`.

**The New Flow:**
1.  User selects "HR Assistant" (Agent).
2.  Frontend knows this Agent is linked to `vault_hr_01`.
3.  User asks: "How many holidays?"
4.  **API Call:**
    ```http
    POST /chat
    {
      "message": "How many holidays?",
      "vault_id": "vault_hr_01"   <-- The Filter
    }
    ```
5.  **System:**
    *   Filters vector search: `WHERE metadata.vault_id = 'vault_hr_01'`
    *   Generates answer ONLY from those docs.

---

## 4. Agent Management (Advanced Layer)

You asked: *"Do we have a Agent management too? Agent name, linked vault"*
*   **Current Status:** No. Currently, you just have a raw "Chat" endpoint.
*   **Recommendation:** Yes, you *should* have an Agent Management layer.

**Why?**
*   You might want an "HR Bot" (Formal tone, HR Vault) and a "Tech Buddy" (Casual tone, Tech Vault).
*   They use the *same* underlying RAG engine, but different *configurations*.

**Proposed Data Structure:**
```json
// Agent Configuration
{
  "agent_id": "agent_007",
  "name": "HR Assistant",
  "system_prompt": "You are a helpful HR assistant. Be polite.",
  "linked_vault_id": "vault_hr_01"
}
```

**Frontend Workflow for Agents:**
1.  **Create Agent:** User names it "Sales Bot", selects "Sales Vault" from a dropdown, sets a System Prompt ("Be aggressive").
2.  **Chat Interface:** User sees a list of Agents. Clicks "Sales Bot".
3.  **Backend:** When chatting with "Sales Bot", the backend automatically applies the "Sales Vault" filter and the "Be aggressive" system prompt.

## Summary of Missing Pieces (To Build)

To enable this workflow for your Frontend team, we need to upgrade the API:

1.  **Update `/ingest`**: Add `vault_id` support.
2.  **Update `/documents`**: Add `vault_id` filtering to the list.
3.  **Update `/chat`**: Add `vault_id` filtering to the search.
4.  **(Optional but Recommended) `/agents`**: Endpoints to save Agent configurations (Name -> Vault ID mapping).
