"""Test script to verify API provider and model availability."""

import requests
import json

API_KEY = "sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD"
API_BASE = "https://api.bltcy.ai"
MODEL = "gpt-5-nano-2025-08-07"

def test_list_models():
    """Test listing available models."""
    print("=" * 70)
    print("Testing API Provider: https://api.bltcy.ai")
    print("=" * 70)
    
    print("\n1. Testing /v1/models endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/v1/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            print(f"\n✅ Found {len(models)} models")
            
            # Look for the specific model
            model_ids = [m.get("id") for m in models]
            
            print("\nAvailable models:")
            for model_id in sorted(model_ids)[:20]:  # Show first 20
                marker = "👉" if MODEL in model_id else "  "
                print(f"{marker} {model_id}")
            
            if len(models) > 20:
                print(f"... and {len(models) - 20} more")
            
            # Check if our model exists
            if MODEL in model_ids:
                print(f"\n✅ Model '{MODEL}' is available!")
                return True
            else:
                print(f"\n⚠️  Model '{MODEL}' not found in available models")
                
                # Check for similar models
                similar = [m for m in model_ids if "gpt" in m.lower() and "nano" in m.lower()]
                if similar:
                    print("\nSimilar models found:")
                    for m in similar:
                        print(f"  - {m}")
                
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_chat_completion():
    """Test chat completion with the model."""
    print("\n" + "=" * 70)
    print(f"2. Testing chat completion with model: {MODEL}")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": "Say 'Hello, this is a test!'"}
                ],
                "max_tokens": 50
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"\n✅ Chat completion successful!")
            print(f"Response: {message}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to parse error message
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "")
                if error_msg:
                    print(f"\nError message: {error_msg}")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_embeddings():
    """Test embeddings endpoint."""
    print("\n" + "=" * 70)
    print("3. Testing embeddings with model: text-embedding-3-small")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-3-small",
                "input": "This is a test"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding", [])
            print(f"\n✅ Embeddings successful!")
            print(f"Embedding dimension: {len(embedding)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all tests."""
    results = {
        "models": test_list_models(),
        "chat": test_chat_completion(),
        "embeddings": test_embeddings()
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name.title()}")
    
    print("=" * 70)
    
    if results["chat"]:
        print("\n✅ Your model 'gpt-5-nano-2025-08-07' works!")
        print("   No changes needed in Railway.")
    else:
        print("\n⚠️  Model 'gpt-5-nano-2025-08-07' may not be available.")
        print("   Check the available models list above.")
        print("   You may need to update CHAT_MODEL in Railway.")

if __name__ == "__main__":
    main()
