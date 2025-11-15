"""Simple API test script for local deployment testing."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_create_session():
    """Test session creation."""
    print("\n=== Testing Session Creation ===")
    response = requests.post(f"{BASE_URL}/api/v1/sessions")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return data.get("session_id") if response.status_code == 200 else None

def test_ingest_document(session_id):
    """Test document ingestion."""
    print("\n=== Testing Document Ingestion ===")
    payload = {
        "content": "LlamaIndex is a data framework for LLM applications. It provides tools for ingesting, structuring, and accessing private or domain-specific data.",
        "metadata": {
            "source": "test",
            "title": "LlamaIndex Introduction"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/ingest",
        params={"session_id": session_id},
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_chat(session_id):
    """Test chat endpoint."""
    print("\n=== Testing Chat ===")
    payload = {
        "message": "What is LlamaIndex?",
        "temperature": 0.3,
        "top_k": 3
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        params={"session_id": session_id},
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_documents(session_id):
    """Test getting documents."""
    print("\n=== Testing Get Documents ===")
    response = requests.get(
        f"{BASE_URL}/api/v1/documents",
        params={"session_id": session_id}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def main():
    """Run all tests."""
    print("=" * 60)
    print("RAG API Local Deployment Test")
    print("=" * 60)
    
    try:
        # Test health
        if not test_health():
            print("\n❌ Health check failed!")
            return
        
        # Create session
        session_id = test_create_session()
        if not session_id:
            print("\n❌ Session creation failed!")
            return
        
        print(f"\n✅ Session created: {session_id}")
        
        # Wait a moment for session to be ready
        time.sleep(1)
        
        # Ingest document
        if not test_ingest_document(session_id):
            print("\n❌ Document ingestion failed!")
            return
        
        print("\n✅ Document ingested successfully")
        
        # Wait for indexing
        time.sleep(2)
        
        # Test chat
        if not test_chat(session_id):
            print("\n❌ Chat failed!")
            return
        
        print("\n✅ Chat completed successfully")
        
        # Get documents
        if not test_get_documents(session_id):
            print("\n❌ Get documents failed!")
            return
        
        print("\n✅ Get documents successful")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error! Make sure the API is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
