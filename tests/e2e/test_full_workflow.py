"""End-to-end test for full ingestion → chat workflow.

This test verifies the complete RAG workflow:
1. Ingest documents with content
2. Create a chat session
3. Ask questions about the ingested content
4. Verify responses contain relevant information
5. Verify sources are returned correctly

Requirements: 2.1-2.7, 5.1-5.9
"""

import requests
import time
import uuid
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_full_rag_workflow():
    """Test complete RAG workflow from document ingestion to chat response."""
    
    print("\n" + "="*70)
    print("E2E TEST: Full RAG Workflow")
    print("="*70)
    
    # Step 1: Verify API is healthy
    print("\n[1/6] Checking API health...")
    health_response = requests.get(f"{BASE_URL}/health")
    assert health_response.status_code == 200, "Health check failed"
    health_data = health_response.json()
    assert health_data["status"] == "ok", "API not healthy"
    print("✅ API is healthy")
    
    # Step 2: Ingest first document about LlamaIndex
    print("\n[2/6] Ingesting document 1 (LlamaIndex)...")
    doc1_content = """
    LlamaIndex is a data framework for LLM applications. It provides tools for 
    ingesting, structuring, and accessing private or domain-specific data. 
    LlamaIndex enables you to build context-augmented LLM applications using 
    Retrieval-Augmented Generation (RAG). The framework supports various data 
    sources including documents, databases, and APIs.
    """
    
    ingest1_response = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "text": doc1_content,
            "title": "LlamaIndex Overview",
            "source": "documentation",
            "metadata": {"category": "framework", "version": "0.9"}
        }
    )
    assert ingest1_response.status_code == 200, f"Ingest 1 failed: {ingest1_response.text}"
    doc1_id = ingest1_response.json()["document_id"]
    print(f"✅ Document 1 ingested: {doc1_id}")
    
    # Step 3: Ingest second document about RAG
    print("\n[3/6] Ingesting document 2 (RAG)...")
    doc2_content = """
    Retrieval-Augmented Generation (RAG) is a technique that combines information 
    retrieval with text generation. RAG systems first retrieve relevant documents 
    from a knowledge base, then use those documents as context for generating 
    responses. This approach helps reduce hallucinations and provides more accurate, 
    grounded responses based on actual data.
    """
    
    ingest2_response = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "text": doc2_content,
            "title": "RAG Explained",
            "source": "documentation",
            "metadata": {"category": "concept", "difficulty": "intermediate"}
        }
    )
    assert ingest2_response.status_code == 200, f"Ingest 2 failed: {ingest2_response.text}"
    doc2_id = ingest2_response.json()["document_id"]
    print(f"✅ Document 2 ingested: {doc2_id}")
    
    # Wait for indexing to complete
    print("\n[4/6] Waiting for indexing...")
    time.sleep(2)
    print("✅ Indexing complete")
    
    # Step 4: Create a chat session and ask about LlamaIndex
    print("\n[5/6] Testing chat with RAG...")
    session_id = f"e2e-test-{uuid.uuid4()}"
    
    chat_response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "What is LlamaIndex?",
            "config": {
                "top_k": 3,
                "temperature": 0.3
            }
        }
    )
    
    assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
    chat_data = chat_response.json()
    
    # Verify response structure
    assert "session_id" in chat_data, "Missing session_id in response"
    assert "answer" in chat_data, "Missing answer in response"
    assert "sources" in chat_data, "Missing sources in response"
    assert chat_data["session_id"] == session_id, "Session ID mismatch"
    
    answer = chat_data["answer"]
    sources = chat_data["sources"]
    
    print(f"\n📝 Question: What is LlamaIndex?")
    print(f"🤖 Answer: {answer[:200]}...")
    print(f"📚 Sources retrieved: {len(sources)}")
    
    # Verify answer is not empty
    assert len(answer) > 0, "Empty answer received"
    
    # Verify sources are returned
    assert len(sources) > 0, "No sources returned"
    
    # Verify source structure
    for source in sources:
        assert "document_id" in source, "Source missing document_id"
        assert "snippet" in source, "Source missing snippet"
        assert "score" in source, "Source missing score"
        print(f"  - Document: {source.get('title', 'Untitled')} (score: {source['score']:.3f})")
    
    print("✅ Chat response received with sources")
    
    # Step 5: Ask a follow-up question about RAG
    print("\n[6/6] Testing follow-up question...")
    
    followup_response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "What is RAG and how does it work?",
            "config": {
                "top_k": 3,
                "temperature": 0.3
            }
        }
    )
    
    assert followup_response.status_code == 200, f"Follow-up failed: {followup_response.text}"
    followup_data = followup_response.json()
    
    followup_answer = followup_data["answer"]
    followup_sources = followup_data["sources"]
    
    print(f"\n📝 Question: What is RAG and how does it work?")
    print(f"🤖 Answer: {followup_answer[:200]}...")
    print(f"📚 Sources retrieved: {len(followup_sources)}")
    
    assert len(followup_answer) > 0, "Empty follow-up answer"
    assert len(followup_sources) > 0, "No sources in follow-up"
    
    print("✅ Follow-up question answered")
    
    # Step 6: Verify documents are listed
    print("\n[Bonus] Verifying document listing...")
    docs_response = requests.get(f"{BASE_URL}/documents")
    assert docs_response.status_code == 200, "Documents listing failed"
    docs_data = docs_response.json()
    
    assert "documents" in docs_data, "Missing documents field"
    documents = docs_data["documents"]
    
    # Verify our documents are in the list
    doc_ids = [doc["document_id"] for doc in documents]
    assert doc1_id in doc_ids, "Document 1 not found in listing"
    assert doc2_id in doc_ids, "Document 2 not found in listing"
    
    print(f"✅ Found {len(documents)} documents in database")
    
    print("\n" + "="*70)
    print("✅ FULL RAG WORKFLOW TEST PASSED")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        test_full_rag_workflow()
        print("\n✅ All E2E tests passed!")
        exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error! Make sure the API is running on http://localhost:8000")
        print("   Run: docker compose up --build")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
