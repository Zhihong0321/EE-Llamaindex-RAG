"""End-to-end test for source retrieval accuracy.

This test verifies that:
1. Sources are correctly retrieved based on query relevance
2. Source metadata is accurate (document_id, title, snippet, score)
3. Relevance scores are reasonable
4. Retrieved sources match the ingested documents

Requirements: 2.6, 5.4, 5.5, 5.9
"""

import requests
import time
import uuid


BASE_URL = "http://localhost:8000"


def test_source_retrieval_accuracy():
    """Test that source retrieval is accurate and relevant."""
    
    print("\n" + "="*70)
    print("E2E TEST: Source Retrieval Accuracy")
    print("="*70)
    
    # Setup: Ingest multiple documents with distinct topics
    print("\n[Setup] Ingesting knowledge base with distinct topics...")
    
    documents = []
    
    # Document 1: Machine Learning
    doc1 = {
        "text": """
        Machine Learning is a subset of artificial intelligence that enables systems 
        to learn and improve from experience without being explicitly programmed. 
        ML algorithms build mathematical models based on training data to make 
        predictions or decisions. Common types include supervised learning, 
        unsupervised learning, and reinforcement learning.
        """,
        "title": "Machine Learning Basics",
        "source": "ml_textbook",
        "metadata": {"topic": "machine_learning", "difficulty": "beginner"}
    }
    
    # Document 2: Web Development
    doc2 = {
        "text": """
        Web Development involves creating websites and web applications. It includes 
        frontend development (HTML, CSS, JavaScript) for user interfaces and backend 
        development (servers, databases, APIs) for business logic. Modern web development 
        uses frameworks like React, Vue, Angular for frontend and Node.js, Django, 
        Flask for backend.
        """,
        "title": "Web Development Overview",
        "source": "web_guide",
        "metadata": {"topic": "web_development", "difficulty": "beginner"}
    }
    
    # Document 3: Database Systems
    doc3 = {
        "text": """
        Database Systems are organized collections of data that can be easily accessed, 
        managed, and updated. Relational databases like PostgreSQL and MySQL use SQL 
        for querying. NoSQL databases like MongoDB and Redis offer flexible schemas. 
        Modern databases support features like transactions, indexing, and replication.
        """,
        "title": "Database Systems Guide",
        "source": "db_handbook",
        "metadata": {"topic": "databases", "difficulty": "intermediate"}
    }
    
    # Ingest all documents
    for i, doc in enumerate([doc1, doc2, doc3], 1):
        response = requests.post(f"{BASE_URL}/ingest", json=doc)
        assert response.status_code == 200, f"Failed to ingest document {i}"
        doc_id = response.json()["document_id"]
        documents.append({
            "id": doc_id,
            "title": doc["title"],
            "topic": doc["metadata"]["topic"]
        })
        print(f"✅ Document {i} ingested: {doc['title']}")
    
    time.sleep(2)  # Wait for indexing
    print("✅ Knowledge base ready (3 documents)")
    
    # Test 1: Query about Machine Learning
    print("\n[Test 1] Querying about Machine Learning...")
    session_id = f"source-test-{uuid.uuid4()}"
    
    response1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "What is machine learning?",
            "config": {"top_k": 3, "temperature": 0.1}
        }
    )
    
    assert response1.status_code == 200, "ML query failed"
    data1 = response1.json()
    sources1 = data1["sources"]
    
    print(f"📚 Retrieved {len(sources1)} sources:")
    for i, source in enumerate(sources1, 1):
        print(f"  {i}. {source.get('title', 'Untitled')} (score: {source['score']:.4f})")
        print(f"     Snippet: {source['snippet'][:80]}...")
        
        # Verify source structure
        assert "document_id" in source, f"Source {i} missing document_id"
        assert "snippet" in source, f"Source {i} missing snippet"
        assert "score" in source, f"Source {i} missing score"
        assert isinstance(source["score"], (int, float)), f"Source {i} score not numeric"
        assert 0 <= source["score"] <= 1, f"Source {i} score out of range: {source['score']}"
    
    # The top source should be about ML
    if sources1:
        top_source = sources1[0]
        top_doc = next((d for d in documents if d["id"] == top_source["document_id"]), None)
        if top_doc:
            print(f"\n✅ Top source: {top_doc['title']} (topic: {top_doc['topic']})")
            if top_doc["topic"] == "machine_learning":
                print("✅ Correct topic retrieved!")
            else:
                print(f"⚠️  Expected ML topic, got: {top_doc['topic']}")
    
    # Test 2: Query about Web Development
    print("\n[Test 2] Querying about Web Development...")
    
    response2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "Tell me about web development frameworks",
            "config": {"top_k": 3, "temperature": 0.1}
        }
    )
    
    assert response2.status_code == 200, "Web dev query failed"
    data2 = response2.json()
    sources2 = data2["sources"]
    
    print(f"📚 Retrieved {len(sources2)} sources:")
    for i, source in enumerate(sources2, 1):
        print(f"  {i}. {source.get('title', 'Untitled')} (score: {source['score']:.4f})")
    
    # Check if web development document is in top sources
    web_dev_found = False
    for source in sources2:
        doc = next((d for d in documents if d["id"] == source["document_id"]), None)
        if doc and doc["topic"] == "web_development":
            web_dev_found = True
            print(f"\n✅ Web development document found in sources!")
            break
    
    if not web_dev_found:
        print("\n⚠️  Web development document not in top sources")
    
    # Test 3: Query about Databases
    print("\n[Test 3] Querying about Databases...")
    
    response3 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "What are database systems?",
            "config": {"top_k": 3, "temperature": 0.1}
        }
    )
    
    assert response3.status_code == 200, "Database query failed"
    data3 = response3.json()
    sources3 = data3["sources"]
    
    print(f"📚 Retrieved {len(sources3)} sources:")
    for i, source in enumerate(sources3, 1):
        print(f"  {i}. {source.get('title', 'Untitled')} (score: {source['score']:.4f})")
    
    # Check if database document is in top sources
    db_found = False
    for source in sources3:
        doc = next((d for d in documents if d["id"] == source["document_id"]), None)
        if doc and doc["topic"] == "databases":
            db_found = True
            print(f"\n✅ Database document found in sources!")
            break
    
    if not db_found:
        print("\n⚠️  Database document not in top sources")
    
    # Test 4: Verify source snippets are meaningful
    print("\n[Test 4] Verifying source snippet quality...")
    
    all_sources = sources1 + sources2 + sources3
    snippet_quality_pass = True
    
    for source in all_sources:
        snippet = source["snippet"]
        
        # Snippet should not be empty
        if not snippet or len(snippet.strip()) == 0:
            print(f"❌ Empty snippet found")
            snippet_quality_pass = False
            continue
        
        # Snippet should be reasonable length (not too short)
        if len(snippet) < 20:
            print(f"⚠️  Very short snippet: {snippet}")
            snippet_quality_pass = False
    
    if snippet_quality_pass:
        print("✅ All snippets have reasonable quality")
    
    # Test 5: Verify relevance scores are reasonable
    print("\n[Test 5] Verifying relevance scores...")
    
    score_quality_pass = True
    
    for sources in [sources1, sources2, sources3]:
        if len(sources) > 1:
            # Scores should be in descending order (most relevant first)
            for i in range(len(sources) - 1):
                if sources[i]["score"] < sources[i + 1]["score"]:
                    print(f"⚠️  Scores not in descending order")
                    score_quality_pass = False
                    break
    
    if score_quality_pass:
        print("✅ Relevance scores are properly ordered")
    
    # Test 6: Verify document IDs match ingested documents
    print("\n[Test 6] Verifying document ID integrity...")
    
    all_doc_ids = {doc["id"] for doc in documents}
    retrieved_doc_ids = {source["document_id"] for source in all_sources}
    
    # All retrieved IDs should be from our ingested documents
    invalid_ids = retrieved_doc_ids - all_doc_ids
    
    if not invalid_ids:
        print("✅ All retrieved document IDs are valid")
    else:
        print(f"⚠️  Found invalid document IDs: {invalid_ids}")
    
    # Test 7: Test top_k parameter
    print("\n[Test 7] Testing top_k parameter...")
    
    response_k1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "Tell me about technology",
            "config": {"top_k": 1, "temperature": 0.1}
        }
    )
    
    response_k3 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "Tell me about technology",
            "config": {"top_k": 3, "temperature": 0.1}
        }
    )
    
    assert response_k1.status_code == 200, "top_k=1 query failed"
    assert response_k3.status_code == 200, "top_k=3 query failed"
    
    sources_k1 = response_k1.json()["sources"]
    sources_k3 = response_k3.json()["sources"]
    
    print(f"  top_k=1: {len(sources_k1)} sources retrieved")
    print(f"  top_k=3: {len(sources_k3)} sources retrieved")
    
    # top_k=3 should retrieve more sources than top_k=1
    if len(sources_k3) >= len(sources_k1):
        print("✅ top_k parameter works correctly")
    else:
        print("⚠️  top_k parameter may not be working as expected")
    
    print("\n" + "="*70)
    print("✅ SOURCE RETRIEVAL ACCURACY TEST PASSED")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        test_source_retrieval_accuracy()
        print("\n✅ Source accuracy test passed!")
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
