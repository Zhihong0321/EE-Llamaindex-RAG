# Backend Implementation Request: Vault Management Endpoints

**Priority**: HIGH  
**Date**: November 21, 2025  
**Requested By**: Frontend Team  
**Status**: 🔴 BLOCKING FEATURE

---

## Problem Statement

The frontend has a complete vault management UI that is currently disabled because the backend API is missing vault CRUD endpoints. Users are getting 404 errors when trying to create or manage vaults.

**Current State**: Backend supports `vault_id` as an optional parameter in `/ingest`, `/chat`, and `/documents` endpoints, but there's no way to create or manage vaults.

**Desired State**: Full vault management capability with CRUD operations.

---

## Required API Endpoints

### 1. Create Vault
```http
POST /vaults
Content-Type: application/json

Request Body:
{
  "name": "string",           // Required, min 1 char
  "description": "string"     // Optional
}

Response (201 Created):
{
  "vault_id": "string",       // UUID or unique identifier
  "name": "string",
  "description": "string",
  "created_at": "2025-11-21T10:30:00Z",
  "document_count": 0
}

Error Responses:
- 400: Invalid request (missing name, validation failed)
- 409: Vault with same name already exists
- 500: Server error
```

### 2. List All Vaults
```http
GET /vaults

Response (200 OK):
[
  {
    "vault_id": "string",
    "name": "string",
    "description": "string",
    "created_at": "2025-11-21T10:30:00Z",
    "document_count": 5
  },
  ...
]

Error Responses:
- 500: Server error
```

### 3. Get Single Vault
```http
GET /vaults/{vault_id}

Response (200 OK):
{
  "vault_id": "string",
  "name": "string",
  "description": "string",
  "created_at": "2025-11-21T10:30:00Z",
  "document_count": 5,
  "last_updated": "2025-11-21T15:45:00Z"
}

Error Responses:
- 404: Vault not found
- 500: Server error
```

### 4. Delete Vault
```http
DELETE /vaults/{vault_id}

Response (200 OK):
{
  "vault_id": "string",
  "status": "deleted"
}

Error Responses:
- 404: Vault not found
- 409: Cannot delete vault with documents (optional - or cascade delete)
- 500: Server error
```

---

## Database Schema

### Vaults Table
```sql
CREATE TABLE vaults (
    vault_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_vaults_name ON vaults(name);
CREATE INDEX idx_vaults_created_at ON vaults(created_at);
```

### Update Documents Table
```sql
-- Add foreign key constraint to existing documents table
ALTER TABLE documents 
ADD CONSTRAINT fk_vault_id 
FOREIGN KEY (vault_id) 
REFERENCES vaults(vault_id) 
ON DELETE CASCADE;  -- Or SET NULL, depending on requirements

CREATE INDEX idx_documents_vault_id ON documents(vault_id);
```

---

## Integration with Existing Endpoints

### Current Endpoints That Use vault_id

1. **POST /ingest** - Already accepts optional `vault_id`
   - Add validation: If `vault_id` provided, verify vault exists
   - Return 404 if vault doesn't exist

2. **POST /chat** - Already accepts optional `vault_id`
   - Add validation: If `vault_id` provided, verify vault exists
   - Filter context retrieval by vault_id

3. **GET /documents** - Already accepts optional `vault_id` query param
   - Continue filtering by vault_id
   - Works as-is

---

## Business Logic Requirements

### Vault Creation
- Vault names must be unique (case-insensitive recommended)
- Generate UUID for vault_id
- Set created_at timestamp
- Return complete vault object

### Vault Deletion
**Option A - Cascade Delete** (Recommended):
- Delete all documents in the vault
- Delete all embeddings associated with those documents
- Delete the vault record

**Option B - Prevent Deletion**:
- Return 409 error if vault has documents
- Require manual document deletion first

### Vault Filtering
- When `vault_id` is provided in `/chat` or `/ingest`:
  - Verify vault exists (return 404 if not)
  - Filter vector search to only documents in that vault
  - Isolate chat context to vault documents

---

## Frontend Integration (Already Complete)

The frontend already has these components ready:

✅ **API Client**: `frontend/src/api/vaults.ts`
- `createVault(data)` → POST /vaults
- `getVaults()` → GET /vaults
- `getVault(vaultId)` → GET /vaults/{vault_id}
- `deleteVault(vaultId)` → DELETE /vaults/{vault_id}

✅ **UI Components**:
- VaultFormModal - Create/edit vault form
- VaultList - Display all vaults
- VaultSelector - Dropdown for vault selection
- VaultDeleteConfirm - Deletion confirmation dialog

✅ **Pages**:
- VaultManagement - Full vault CRUD interface
- DocumentUpload - Vault selector for document organization

**Once backend endpoints are ready**, we just need to:
1. Uncomment vault navigation link
2. Uncomment vault selector in document upload
3. Deploy frontend update

---

## Testing Requirements

### Unit Tests
- Vault creation with valid data
- Vault creation with duplicate name (409 error)
- Vault creation with missing name (400 error)
- List vaults (empty and with data)
- Get vault by ID (exists and not found)
- Delete vault (with and without documents)

### Integration Tests
- Create vault → Upload document with vault_id → Verify document in vault
- Create vault → Chat with vault_id → Verify context filtering
- Delete vault → Verify documents are handled (cascade or prevent)
- List documents with vault_id filter

### API Tests
- All endpoints return correct status codes
- Response schemas match specification
- Error messages are descriptive
- CORS headers are set correctly

---

## Example Implementation (FastAPI)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()

class VaultCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class VaultResponse(BaseModel):
    vault_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    document_count: int = 0

@router.post("/vaults", response_model=VaultResponse, status_code=201)
async def create_vault(request: VaultCreateRequest):
    """Create a new vault"""
    vault_id = str(uuid.uuid4())
    
    # Check if vault name already exists
    existing = await db.get_vault_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail="Vault with this name already exists")
    
    # Create vault in database
    vault = await db.create_vault(
        vault_id=vault_id,
        name=request.name,
        description=request.description
    )
    
    return VaultResponse(
        vault_id=vault.vault_id,
        name=vault.name,
        description=vault.description,
        created_at=vault.created_at,
        document_count=0
    )

@router.get("/vaults", response_model=list[VaultResponse])
async def list_vaults():
    """List all vaults"""
    vaults = await db.get_all_vaults()
    return [
        VaultResponse(
            vault_id=v.vault_id,
            name=v.name,
            description=v.description,
            created_at=v.created_at,
            document_count=await db.count_documents_in_vault(v.vault_id)
        )
        for v in vaults
    ]

@router.get("/vaults/{vault_id}", response_model=VaultResponse)
async def get_vault(vault_id: str):
    """Get a single vault by ID"""
    vault = await db.get_vault(vault_id)
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    
    return VaultResponse(
        vault_id=vault.vault_id,
        name=vault.name,
        description=vault.description,
        created_at=vault.created_at,
        document_count=await db.count_documents_in_vault(vault_id)
    )

@router.delete("/vaults/{vault_id}")
async def delete_vault(vault_id: str):
    """Delete a vault"""
    vault = await db.get_vault(vault_id)
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    
    # Option A: Cascade delete documents
    await db.delete_vault_with_documents(vault_id)
    
    # Option B: Prevent deletion if has documents
    # doc_count = await db.count_documents_in_vault(vault_id)
    # if doc_count > 0:
    #     raise HTTPException(
    #         status_code=409, 
    #         detail=f"Cannot delete vault with {doc_count} documents"
    #     )
    # await db.delete_vault(vault_id)
    
    return {"vault_id": vault_id, "status": "deleted"}
```

---

## Migration Plan

### Phase 1: Database Setup
1. Create `vaults` table
2. Add foreign key to `documents` table
3. Run migrations on dev/staging

### Phase 2: API Implementation
1. Implement vault CRUD endpoints
2. Add vault validation to existing endpoints
3. Write unit tests

### Phase 3: Testing
1. Test all vault endpoints
2. Test integration with document/chat endpoints
3. Verify error handling

### Phase 4: Deployment
1. Deploy backend to staging
2. Frontend team tests integration
3. Deploy to production
4. Frontend team enables vault UI

---

## Success Criteria

✅ All 4 vault endpoints implemented and working  
✅ Database schema created with proper indexes  
✅ Vault validation added to existing endpoints  
✅ Unit tests passing (>90% coverage)  
✅ Integration tests passing  
✅ API documentation updated (OpenAPI/Swagger)  
✅ Frontend can create, list, and delete vaults  
✅ Documents can be filtered by vault  
✅ Chat context respects vault boundaries  

---

## Timeline Estimate

- **Database Schema**: 1-2 hours
- **API Implementation**: 4-6 hours
- **Testing**: 2-3 hours
- **Documentation**: 1 hour
- **Total**: 1-2 days

---

## Questions for Backend Team

1. **Deletion Strategy**: Should we cascade delete documents or prevent deletion?
2. **Vault Naming**: Case-sensitive or case-insensitive uniqueness?
3. **Default Vault**: Should there be a "default" vault for documents without vault_id?
4. **Permissions**: Do we need user-based vault access control, or is it global?
5. **Migration**: How to handle existing documents without vault_id?

---

## Contact

**Frontend Team Lead**: [Your Name]  
**Documentation**: See `VAULT-404-ISSUE.md` for detailed problem analysis  
**Frontend Code**: All vault UI components are ready in `frontend/src/components/vault/`

---

## References

- Current API: https://eternalgy-rag-llamaindex-production.up.railway.app/docs
- OpenAPI Spec: https://eternalgy-rag-llamaindex-production.up.railway.app/openapi.json
- Frontend Vault API Client: `frontend/src/api/vaults.ts`
- Frontend Vault Components: `frontend/src/components/vault/`
