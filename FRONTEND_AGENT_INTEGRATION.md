# Frontend Agent Integration Guide

## Quick Start

The Agent Management API is now live! Here's everything you need to integrate it with your frontend.

## Base URL

```javascript
const API_BASE = 'http://localhost:8000';  // Development
// const API_BASE = 'https://your-production-url.railway.app';  // Production
```

## API Endpoints

### 1. Create Agent

```javascript
async function createAgent(name, vaultId, systemPrompt) {
  const response = await fetch(`${API_BASE}/agents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: name,
      vault_id: vaultId,
      system_prompt: systemPrompt
    })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create agent: ${response.statusText}`);
  }
  
  return await response.json();
}

// Usage
const agent = await createAgent(
  'Customer Support Bot',
  'vault-uuid-here',
  'You are a helpful customer support agent.'
);
console.log('Created agent:', agent.agent_id);
```

### 2. List All Agents

```javascript
async function listAgents(vaultId = null) {
  const url = vaultId 
    ? `${API_BASE}/agents?vault_id=${vaultId}`
    : `${API_BASE}/agents`;
    
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to list agents: ${response.statusText}`);
  }
  
  return await response.json();
}

// Usage
const allAgents = await listAgents();
const vaultAgents = await listAgents('vault-uuid-here');
```

### 3. Get Single Agent

```javascript
async function getAgent(agentId) {
  const response = await fetch(`${API_BASE}/agents/${agentId}`);
  
  if (response.status === 404) {
    return null;  // Agent not found
  }
  
  if (!response.ok) {
    throw new Error(`Failed to get agent: ${response.statusText}`);
  }
  
  return await response.json();
}

// Usage
const agent = await getAgent('agent-uuid-here');
if (agent) {
  console.log('Agent name:', agent.name);
} else {
  console.log('Agent not found');
}
```

### 4. Delete Agent

```javascript
async function deleteAgent(agentId) {
  const response = await fetch(`${API_BASE}/agents/${agentId}`, {
    method: 'DELETE'
  });
  
  if (response.status === 404) {
    throw new Error('Agent not found');
  }
  
  if (!response.ok) {
    throw new Error(`Failed to delete agent: ${response.statusText}`);
  }
  
  return await response.json();
}

// Usage
const result = await deleteAgent('agent-uuid-here');
console.log(result.message);  // "Agent deleted successfully"
```

## React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function AgentManager({ vaultId }) {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load agents
  useEffect(() => {
    loadAgents();
  }, [vaultId]);

  async function loadAgents() {
    try {
      setLoading(true);
      const url = vaultId 
        ? `${API_BASE}/agents?vault_id=${vaultId}`
        : `${API_BASE}/agents`;
      const response = await fetch(url);
      const data = await response.json();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAgent(formData) {
    try {
      const response = await fetch(`${API_BASE}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          vault_id: vaultId,
          system_prompt: formData.systemPrompt
        })
      });
      
      if (!response.ok) throw new Error('Failed to create agent');
      
      await loadAgents();  // Refresh list
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete agent');
      
      await loadAgents();  // Refresh list
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div>Loading agents...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Agents</h2>
      <ul>
        {agents.map(agent => (
          <li key={agent.agent_id}>
            <strong>{agent.name}</strong>
            <p>{agent.system_prompt}</p>
            <button onClick={() => handleDeleteAgent(agent.agent_id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Response Formats

### Agent Object
```typescript
interface Agent {
  agent_id: string;        // UUID
  name: string;            // Agent name
  vault_id: string;        // Associated vault UUID
  system_prompt: string;   // Agent's system prompt
  created_at: string;      // ISO 8601 timestamp
}
```

### Create Response
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Customer Support Agent",
  "vault_id": "vault-uuid",
  "system_prompt": "You are a helpful agent...",
  "created_at": "2025-11-29T10:30:00Z"
}
```

### Delete Response
```json
{
  "success": true,
  "message": "Agent deleted successfully"
}
```

## Error Handling

```javascript
async function safeApiCall(apiFunction) {
  try {
    return await apiFunction();
  } catch (error) {
    if (error.response) {
      // Server responded with error
      switch (error.response.status) {
        case 404:
          console.error('Agent not found');
          break;
        case 422:
          console.error('Invalid request data');
          break;
        case 500:
          console.error('Server error');
          break;
        default:
          console.error('Unknown error:', error.response.status);
      }
    } else {
      // Network error
      console.error('Network error:', error.message);
    }
    throw error;
  }
}
```

## Validation Rules

### Frontend Validation
Before sending requests, validate:

```javascript
function validateAgentForm(name, vaultId, systemPrompt) {
  const errors = [];
  
  if (!name || name.trim().length === 0) {
    errors.push('Agent name is required');
  }
  
  if (!vaultId || vaultId.trim().length === 0) {
    errors.push('Vault ID is required');
  }
  
  if (!systemPrompt || systemPrompt.trim().length === 0) {
    errors.push('System prompt is required');
  }
  
  return errors;
}
```

## Common Patterns

### 1. Create Agent with Vault Selection

```javascript
async function createAgentWithVaultSelection() {
  // 1. Load available vaults
  const vaults = await fetch(`${API_BASE}/vaults`).then(r => r.json());
  
  // 2. User selects vault
  const selectedVaultId = vaults[0].vault_id;
  
  // 3. Create agent
  const agent = await createAgent(
    'My Agent',
    selectedVaultId,
    'System prompt here'
  );
  
  return agent;
}
```

### 2. Display Agents by Vault

```javascript
async function displayAgentsByVault() {
  const vaults = await fetch(`${API_BASE}/vaults`).then(r => r.json());
  
  for (const vault of vaults) {
    const agents = await listAgents(vault.vault_id);
    console.log(`${vault.name}: ${agents.length} agents`);
  }
}
```

### 3. Agent with Confirmation

```javascript
async function deleteAgentWithConfirmation(agentId) {
  // Get agent details first
  const agent = await getAgent(agentId);
  
  if (!agent) {
    alert('Agent not found');
    return;
  }
  
  // Confirm with user
  const confirmed = confirm(
    `Delete agent "${agent.name}"?\n\n` +
    `This action cannot be undone.`
  );
  
  if (confirmed) {
    await deleteAgent(agentId);
    alert('Agent deleted successfully');
  }
}
```

## Testing

### Manual Testing
1. Open browser console
2. Copy and paste the API functions
3. Test each endpoint:

```javascript
// Test create
const agent = await createAgent('Test Agent', 'vault-id', 'Test prompt');

// Test list
const agents = await listAgents();

// Test get
const singleAgent = await getAgent(agent.agent_id);

// Test delete
await deleteAgent(agent.agent_id);
```

### Automated Testing
Use the provided test script:
```bash
python test_agents_api.py
```

## Troubleshooting

### Agent Creation Fails
- ✅ Check that vault_id exists
- ✅ Ensure all fields are provided
- ✅ Check network tab for error details

### Agent Not Found (404)
- ✅ Verify agent_id is correct
- ✅ Check if agent was deleted
- ✅ Check if vault was deleted (cascade)

### Empty Agent List
- ✅ Verify vault has agents
- ✅ Check vault_id filter is correct
- ✅ Ensure agents were created successfully

## Support

If you encounter issues:
1. Check the browser console for errors
2. Check the network tab for API responses
3. Check server logs for backend errors
4. Refer to API_DOCUMENTATION.md for details

---

**Ready to integrate!** 🚀
