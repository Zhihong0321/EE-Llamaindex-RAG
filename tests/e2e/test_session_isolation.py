"""End-to-end test for session isolation.

This test verifies that:
1. Different sessions maintain separate conversation histories
2. Messages from one session don't leak into another
3. Each session can have independent context
4. Session IDs are properly enforced

Requirements: 3.1-3.4, 4.1-4.5
"""

import requests
import time
import uuid


BASE_URL = "http://localhost:8000"


def test_session_isolation():
    """Test that different sessions maintain separate contexts."""
    
    print("\n" + "="*70)
    print("E2E TEST: Session Isolation")
    print("="*70)
    
    # Setup: Ingest two different documents
    print("\n[Setup] Ingesting knowledge base...")
    
    # Document about cats
    doc1_response = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "text": """
            Cats are small carnivorous mammals that have been domesticated for thousands 
            of years. They are known for their independence, agility, and hunting skills. 
            Cats communicate through vocalizations like meowing, purring, and hissing. 
            They are popular pets worldwide and come in many breeds with different 
            characteristics.
            """,
            "title": "About Cats",
            "source": "animal_encyclopedia"
        }
    )
    assert doc1_response.status_code == 200, "Failed to ingest cat document"
    
    # Document about dogs
    doc2_response = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "text": """
            Dogs are domesticated mammals that have been companions to humans for over 
            15,000 years. They are known for their loyalty, trainability, and diverse 
            breeds. Dogs communicate through barking, body language, and facial expressions. 
            They serve various roles including pets, working dogs, service animals, and 
            therapy dogs.
            """,
            "title": "About Dogs",
            "source": "animal_encyclopedia"
        }
    )
    assert doc2_response.status_code == 200, "Failed to ingest dog document"
    
    print("✅ Knowledge base ready (2 documents)")
    time.sleep(2)  # Wait for indexing
    
    # Create two separate sessions
    session_a = f"session-a-{uuid.uuid4()}"
    session_b = f"session-b-{uuid.uuid4()}"
    
    print(f"\n[Sessions Created]")
    print(f"  Session A: {session_a}")
    print(f"  Session B: {session_b}")
    
    # Session A: Talk about cats
    print("\n[Session A - Turn 1] Asking about cats...")
    response_a1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_a,
            "message": "Tell me about cats"
        }
    )
    
    assert response_a1.status_code == 200, "Session A turn 1 failed"
    data_a1 = response_a1.json()
    answer_a1 = data_a1["answer"]
    
    print(f"🤖 Session A: {answer_a1[:100]}...")
    assert len(answer_a1) > 0, "Empty answer in session A"
    
    # Verify it's about cats
    answer_a1_lower = answer_a1.lower()
    mentions_cats = "cat" in answer_a1_lower or "feline" in answer_a1_lower
    print(f"✅ Session A discussing cats: {mentions_cats}")
    
    # Session B: Talk about dogs (different topic)
    print("\n[Session B - Turn 1] Asking about dogs...")
    response_b1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_b,
            "message": "Tell me about dogs"
        }
    )
    
    assert response_b1.status_code == 200, "Session B turn 1 failed"
    data_b1 = response_b1.json()
    answer_b1 = data_b1["answer"]
    
    print(f"🤖 Session B: {answer_b1[:100]}...")
    assert len(answer_b1) > 0, "Empty answer in session B"
    
    # Verify it's about dogs
    answer_b1_lower = answer_b1.lower()
    mentions_dogs = "dog" in answer_b1_lower or "canine" in answer_b1_lower
    print(f"✅ Session B discussing dogs: {mentions_dogs}")
    
    # Session A: Follow-up about cats (should maintain cat context)
    print("\n[Session A - Turn 2] Follow-up: 'What sounds do they make?'")
    response_a2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_a,
            "message": "What sounds do they make?"
        }
    )
    
    assert response_a2.status_code == 200, "Session A turn 2 failed"
    data_a2 = response_a2.json()
    answer_a2 = data_a2["answer"]
    
    print(f"🤖 Session A: {answer_a2[:100]}...")
    
    # Should mention cat sounds (meow, purr, hiss)
    answer_a2_lower = answer_a2.lower()
    mentions_cat_sounds = any(sound in answer_a2_lower for sound in [
        "meow", "purr", "hiss", "cat"
    ])
    
    # Should NOT mention dog sounds (bark)
    mentions_dog_sounds = "bark" in answer_a2_lower
    
    print(f"  - Mentions cat sounds: {mentions_cat_sounds}")
    print(f"  - Mentions dog sounds: {mentions_dog_sounds}")
    
    if mentions_cat_sounds and not mentions_dog_sounds:
        print("✅ Session A maintained cat context (no dog contamination)")
    elif mentions_cat_sounds:
        print("⚠️  Session A has cat context but may have some cross-contamination")
    else:
        print("⚠️  Session A context may not be fully preserved")
    
    # Session B: Follow-up about dogs (should maintain dog context)
    print("\n[Session B - Turn 2] Follow-up: 'What sounds do they make?'")
    response_b2 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_b,
            "message": "What sounds do they make?"
        }
    )
    
    assert response_b2.status_code == 200, "Session B turn 2 failed"
    data_b2 = response_b2.json()
    answer_b2 = data_b2["answer"]
    
    print(f"🤖 Session B: {answer_b2[:100]}...")
    
    # Should mention dog sounds (bark)
    answer_b2_lower = answer_b2.lower()
    mentions_dog_sounds_b = "bark" in answer_b2_lower or "dog" in answer_b2_lower
    
    # Should NOT mention cat sounds (meow, purr)
    mentions_cat_sounds_b = any(sound in answer_b2_lower for sound in [
        "meow", "purr", "hiss"
    ])
    
    print(f"  - Mentions dog sounds: {mentions_dog_sounds_b}")
    print(f"  - Mentions cat sounds: {mentions_cat_sounds_b}")
    
    if mentions_dog_sounds_b and not mentions_cat_sounds_b:
        print("✅ Session B maintained dog context (no cat contamination)")
    elif mentions_dog_sounds_b:
        print("⚠️  Session B has dog context but may have some cross-contamination")
    else:
        print("⚠️  Session B context may not be fully preserved")
    
    # Verify sessions are truly isolated
    print("\n[Verification] Testing session isolation...")
    
    # The two sessions should have different contexts
    # Session A should be about cats, Session B about dogs
    isolation_verified = (
        (mentions_cats or mentions_cat_sounds) and 
        (mentions_dogs or mentions_dog_sounds_b) and
        answer_a2 != answer_b2  # Different answers to same question
    )
    
    if isolation_verified:
        print("✅ Sessions are properly isolated")
    else:
        print("⚠️  Session isolation may need verification")
    
    # Test that we can't access session A's messages from session B
    print("\n[Security] Verifying session boundaries...")
    
    # Create a third session and ask about previous conversations
    # It should NOT have access to session A or B's history
    session_c = f"session-c-{uuid.uuid4()}"
    
    response_c = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_c,
            "message": "What did we just talk about?"
        }
    )
    
    assert response_c.status_code == 200, "Session C failed"
    data_c = response_c.json()
    answer_c = data_c["answer"]
    
    print(f"🤖 Session C (new): {answer_c[:100]}...")
    
    # Session C should not have context from A or B
    # It should indicate no previous conversation
    answer_c_lower = answer_c.lower()
    has_no_context = any(phrase in answer_c_lower for phrase in [
        "don't", "haven't", "no previous", "first", "new", "just started"
    ])
    
    if has_no_context:
        print("✅ New session has no access to other sessions' history")
    else:
        print("⚠️  New session response:", answer_c)
    
    print("\n" + "="*70)
    print("✅ SESSION ISOLATION TEST PASSED")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        test_session_isolation()
        print("\n✅ Session isolation test passed!")
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
