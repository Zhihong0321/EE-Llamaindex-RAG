"""Test script for Agent Management API endpoints."""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def test_agents_api():
    """Test all agent management endpoints."""
    
    print("=" * 60)
    print("Testing Agent Management API")
    print("=" * 60)
    
    # Step 1: Create a test vault first (agents need a vault)
    print("\n1. Creating test vault...")
    vault_data = {
        "name": f"Test Vault for Agents {datetime.now().isoformat()}",
        "description": "Test vault for agent testing"
    }
    
    response = requests.post(f"{BASE_URL}/vaults", json=vault_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        vault = response.json()
        vault_id = vault["vault_id"]
        print(f"✓ Vault created: {vault_id}")
        print(f"  Name: {vault['name']}")
    else:
        print(f"✗ Failed to create vault: {response.text}")
        return
    
    # Step 2: Create an agent
    print("\n2. Creating agent...")
    agent_data = {
        "name": "Customer Support Agent",
        "vault_id": vault_id,
        "system_prompt": "You are a helpful customer support agent. Be polite and professional."
    }
    
    response = requests.post(f"{BASE_URL}/agents", json=agent_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agent = response.json()
        agent_id = agent["agent_id"]
        print(f"✓ Agent created: {agent_id}")
        print(f"  Name: {agent['name']}")
        print(f"  Vault ID: {agent['vault_id']}")
        print(f"  System Prompt: {agent['system_prompt'][:50]}...")
        print(f"  Created At: {agent['created_at']}")
    else:
        print(f"✗ Failed to create agent: {response.text}")
        return
    
    # Step 3: Create another agent
    print("\n3. Creating second agent...")
    agent_data2 = {
        "name": "Technical Support Agent",
        "vault_id": vault_id,
        "system_prompt": "You are a technical support specialist. Provide detailed technical solutions."
    }
    
    response = requests.post(f"{BASE_URL}/agents", json=agent_data2)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agent2 = response.json()
        agent2_id = agent2["agent_id"]
        print(f"✓ Second agent created: {agent2_id}")
        print(f"  Name: {agent2['name']}")
    else:
        print(f"✗ Failed to create second agent: {response.text}")
    
    # Step 4: List all agents
    print("\n4. Listing all agents...")
    response = requests.get(f"{BASE_URL}/agents")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✓ Retrieved {len(agents)} agents")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['agent_id']})")
    else:
        print(f"✗ Failed to list agents: {response.text}")
    
    # Step 5: List agents filtered by vault
    print(f"\n5. Listing agents for vault {vault_id}...")
    response = requests.get(f"{BASE_URL}/agents?vault_id={vault_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✓ Retrieved {len(agents)} agents for this vault")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['agent_id']})")
    else:
        print(f"✗ Failed to list agents by vault: {response.text}")
    
    # Step 6: Get specific agent
    print(f"\n6. Getting agent {agent_id}...")
    response = requests.get(f"{BASE_URL}/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agent = response.json()
        print(f"✓ Agent retrieved")
        print(f"  Name: {agent['name']}")
        print(f"  Vault ID: {agent['vault_id']}")
        print(f"  System Prompt: {agent['system_prompt']}")
    else:
        print(f"✗ Failed to get agent: {response.text}")
    
    # Step 7: Delete first agent
    print(f"\n7. Deleting agent {agent_id}...")
    response = requests.delete(f"{BASE_URL}/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Agent deleted")
        print(f"  Success: {result['success']}")
        print(f"  Message: {result['message']}")
    else:
        print(f"✗ Failed to delete agent: {response.text}")
    
    # Step 8: Verify deletion
    print(f"\n8. Verifying agent deletion...")
    response = requests.get(f"{BASE_URL}/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"✓ Agent correctly not found (deleted)")
    else:
        print(f"✗ Agent still exists or unexpected error")
    
    # Step 9: List agents again
    print(f"\n9. Listing agents after deletion...")
    response = requests.get(f"{BASE_URL}/agents?vault_id={vault_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✓ Retrieved {len(agents)} agents (should be 1)")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['agent_id']})")
    else:
        print(f"✗ Failed to list agents: {response.text}")
    
    # Cleanup: Delete test vault (will cascade delete remaining agents)
    print(f"\n10. Cleaning up - deleting test vault...")
    response = requests.delete(f"{BASE_URL}/vaults/{vault_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ Test vault deleted (agents cascade deleted)")
    else:
        print(f"✗ Failed to delete vault: {response.text}")
    
    print("\n" + "=" * 60)
    print("Agent Management API Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_agents_api()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API server")
        print("  Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
