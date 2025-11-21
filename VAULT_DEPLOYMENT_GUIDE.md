# Vault Feature Deployment Guide

**Quick Reference for Deploying Vault Management**

---

## 🚀 Deployment Steps

### 1. Run Database Migration

**On Railway (Production)**:
```bash
# Railway will auto-run migrations on deploy, but you can also run manually:
railway run alembic upgrade head
```

**On Local/Staging**:
```bash
alembic upgrade head
```

This creates:
- `vaults` table
- Adds `vault_id` column to `documents` table
- Creates indexes and foreign key constraints

---

### 2. Deploy Backend

**Push to Railway**:
```bash
git add .
git commit -m "feat: Add vault management endpoints"
git push railway main
```

**Or deploy via Railway CLI**:
```bash
railway up
```

---

### 3. Verify Deployment

**Check API Documentation**:
```
https://your-domain.railway.app/docs
```

Look for new endpoints:
- POST /vaults
- GET /vaults
- GET /vaults/{vault_id}
- DELETE /vaults/{vault_id}

**Test Vault Creation**:
```bash
curl -X POST https://your-domain.railway.app/vaults \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Vault", "description": "Testing"}'
```

Expected response (201):
```json
{
  "vault_id": "uuid-here",
  "name": "Test Vault",
  "description": "Testing",
  "created_at": "2025-11-21T...",
  "document_count": 0
}
```

---

### 4. Frontend Integration

Once backend is deployed and verified:

1. **Enable Vault UI** in frontend:
   - Uncomment vault navigation link
   - Uncomment vault selector in document upload

2. **Update API calls** to use vault_id:
   ```typescript
   // Document upload with vault
   await ingestDocument({
     text: content,
     title: title,
     vault_id: selectedVaultId  // Add this
   });
   
   // Chat with vault filtering
   await sendMessage({
     session_id: sessionId,
     message: userMessage,
     vault_id: selectedVaultId  // Add this
   });
   ```

3. **Deploy frontend** with vault UI enabled

---

## 🧪 Testing Checklist

### Backend Tests
- [ ] Unit tests pass: `pytest tests/unit/test_vault_service.py -v`
- [ ] Integration tests pass: `pytest tests/integration/test_vaults_endpoint.py -v`
- [ ] All endpoints return correct status codes
- [ ] Swagger UI shows vault endpoints

### Frontend Tests
- [ ] Can create vault from UI
- [ ] Can list vaults in dropdown
- [ ] Can upload document to specific vault
- [ ] Can filter documents by vault
- [ ] Can delete vault (with confirmation)
- [ ] Chat respects vault filtering

---

## 🔍 Troubleshooting

### Migration Fails
```bash
# Check current migration version
alembic current

# If stuck, check database connection
railway run python -c "import asyncpg; print('DB accessible')"

# Force migration
railway run alembic upgrade head --sql  # Preview SQL
railway run alembic upgrade head        # Apply
```

### Vault Endpoints Return 500
- Check logs: `railway logs`
- Verify VaultService is wired in main.py
- Verify migration ran successfully
- Check database has `vaults` table

### Foreign Key Constraint Errors
- Ensure migration 002 ran after 001
- Check `documents.vault_id` column exists
- Verify foreign key constraint exists:
  ```sql
  SELECT constraint_name 
  FROM information_schema.table_constraints 
  WHERE table_name = 'documents' 
  AND constraint_type = 'FOREIGN KEY';
  ```

---

## 📊 Monitoring

### Key Metrics to Watch
- Vault creation rate
- Documents per vault
- Vault deletion frequency
- Query performance with vault filtering

### Database Queries
```sql
-- Count vaults
SELECT COUNT(*) FROM vaults;

-- Documents per vault
SELECT v.name, COUNT(d.id) as doc_count
FROM vaults v
LEFT JOIN documents d ON v.vault_id = d.vault_id
GROUP BY v.vault_id, v.name;

-- Orphaned documents (should be 0)
SELECT COUNT(*) FROM documents WHERE vault_id IS NOT NULL 
AND vault_id NOT IN (SELECT vault_id FROM vaults);
```

---

## 🔄 Rollback Plan

If issues occur, rollback migration:

```bash
# Rollback to previous version
alembic downgrade -1

# Or rollback to specific version
alembic downgrade 001
```

This will:
- Drop `vaults` table
- Remove `vault_id` column from `documents`
- Remove foreign key constraint

**Note**: Rollback will delete all vault data!

---

## ✅ Success Criteria

Deployment is successful when:
- ✅ All 4 vault endpoints accessible
- ✅ Can create vault via API
- ✅ Can list vaults with document counts
- ✅ Can delete vault (cascades to documents)
- ✅ Documents can be assigned to vaults
- ✅ Chat filtering works with vault_id
- ✅ No errors in logs
- ✅ Frontend can use all vault features

---

## 📞 Support

**Backend Issues**: Check `VAULT_IMPLEMENTATION_COMPLETE.md`  
**API Reference**: Check `API_DOCUMENTATION.md`  
**Original Request**: Check `BACKEND-VAULT-IMPLEMENTATION-REQUEST.md`

---

**Estimated Deployment Time**: 10-15 minutes  
**Estimated Testing Time**: 15-20 minutes  
**Total**: ~30 minutes
