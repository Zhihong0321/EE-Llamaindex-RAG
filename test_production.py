"""Production API test script for Railway deployment."""

import requests
import json
import time
import sys

# Production URL
BASE_URL = "https://eternalgy-rag-llamaindex-production.up.railway.app"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_create_session():
    """Test session creation (sessions are auto-created, so we just generate an ID)."""
    print("\n=== Testing Session Creation ===")
    import uuid
    session_id = str(uuid.uuid4())
    print(f"Generated session ID: {session_id}")
    print("Note: Sessions are created automatically on first use")
    return session_id

def test_ingest_document(session_id):
    """Test document ingestion."""
    print("\n=== Testing Document Ingestion ===")
    payload = {
        "text": "LlamaIndex is a data framework for LLM applications. It provides tools for ingesting, structuring, and accessing private or domain-specific data. It enables RAG (Retrieval-Augmented Generation) workflows.",
        "title": "LlamaIndex Introduction - Production Test",
        "source": "production_test"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/ingest",
            params={"session_id": session_id},
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_chat(session_id):
    """Test chat endpoint."""
    print("\n=== Testing Chat ===")
    payload = {
        "session_id": session_id,
        "message": "What is LlamaIndex and what does it do?",
        "config": {
            "temperature": 0.3,
            "top_k": 3
        }
    }
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check for sources
        if response.status_code == 200:
            sources = data.get("sources", [])
            print(f"\n📚 Sources returned: {len(sources)}")
            for i, source in enumerate(sources, 1):
                score = source.get('score', 0)
                title = source.get('metadata', {}).get('title', 'Untitled')
                print(f"  {i}. Score: {score:.3f} - {title}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_get_documents(session_id):
    """Test getting documents."""
    print("\n=== Testing Get Documents ===")
    try:
        response = requests.get(
            f"{BASE_URL}/documents",
            params={"session_id": session_id},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            docs = data.get("documents", [])
            print(f"\n📄 Total documents: {len(docs)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_multi_turn_conversation(session_id):
    """Test multi-turn conversation."""
    print("\n=== Testing Multi-Turn Conversation ===")
    
    questions = [
        "What is RAG?",
        "How does it relate to LlamaIndex?",
        "Can you summarize what we discussed?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Turn {i}: {question} ---")
        payload = {
            "session_id": session_id,
            "message": question,
            "config": {
                "temperature": 0.3,
                "top_k": 3
            }
        }
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json=payload,
                timeout=30
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data.get('response', 'No response')[:200]}...")
            else:
                print(f"Error: {response.text}")
                return False
            
            time.sleep(1)  # Brief pause between turns
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    return True

def main():
    """Run all production tests."""
    print("=" * 70)
    print("RAG API Production Deployment Test")
    print(f"Testing: {BASE_URL}")
    print("=" * 70)
    
    results = {
        "health": False,
        "session": False,
        "ingest": False,
        "chat": False,
        "documents": False,
        "multi_turn": False
    }
    
    try:
        # Test health
        print("\n🔍 Step 1: Health Check")
        results["health"] = test_health()
        if not results["health"]:
            print("\n❌ Health check failed! Server may be down.")
            sys.exit(1)
        print("✅ Health check passed")
        
        # Create session
        print("\n🔍 Step 2: Session Creation")
        session_id = test_create_session()
        if not session_id:
            print("\n❌ Session creation failed!")
            sys.exit(1)
        results["session"] = True
        print(f"✅ Session created: {session_id}")
        
        # Wait for session to be ready
        time.sleep(1)
        
        # Ingest document
        print("\n🔍 Step 3: Document Ingestion")
        results["ingest"] = test_ingest_document(session_id)
        if not results["ingest"]:
            print("\n❌ Document ingestion failed!")
            sys.exit(1)
        print("✅ Document ingested successfully")
        
        # Wait for indexing
        print("\n⏳ Waiting for document indexing...")
        time.sleep(3)
        
        # Test chat
        print("\n🔍 Step 4: Chat Query")
        results["chat"] = test_chat(session_id)
        if not results["chat"]:
            print("\n❌ Chat failed!")
            sys.exit(1)
        print("✅ Chat completed successfully")
        
        # Get documents
        print("\n🔍 Step 5: List Documents")
        results["documents"] = test_get_documents(session_id)
        if not results["documents"]:
            print("\n❌ Get documents failed!")
            sys.exit(1)
        print("✅ Get documents successful")
        
        # Multi-turn conversation
        print("\n🔍 Step 6: Multi-Turn Conversation")
        results["multi_turn"] = test_multi_turn_conversation(session_id)
        if not results["multi_turn"]:
            print("\n❌ Multi-turn conversation failed!")
            sys.exit(1)
        print("✅ Multi-turn conversation successful")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        all_passed = all(results.values())
        print("=" * 70)
        if all_passed:
            print("🎉 ALL TESTS PASSED! Production API is working correctly.")
        else:
            print("⚠️  SOME TESTS FAILED! Check the output above.")
        print("=" * 70)
        
        sys.exit(0 if all_passed else 1)
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error! Cannot reach {BASE_URL}")
        print("   - Check if the server is running")
        print("   - Verify the URL is correct")
        print("   - Check your internet connection")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
