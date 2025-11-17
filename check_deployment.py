"""Check Railway deployment status."""

import requests
import time
import sys

BASE_URL = "https://eternalgy-rag-llamaindex-production.up.railway.app"

def check_health():
    """Check if the health endpoint is responding."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, str(e)

def main():
    """Monitor deployment status."""
    print("=" * 60)
    print("Railway Deployment Monitor")
    print(f"URL: {BASE_URL}")
    print("=" * 60)
    print("\nChecking deployment status...")
    print("(Press Ctrl+C to stop)\n")
    
    attempt = 0
    max_attempts = 60  # 5 minutes with 5-second intervals
    
    while attempt < max_attempts:
        attempt += 1
        success, result = check_health()
        
        timestamp = time.strftime("%H:%M:%S")
        
        if success:
            print(f"\n✅ [{timestamp}] Deployment successful!")
            print(f"Response: {result}")
            print("\n" + "=" * 60)
            print("🎉 Server is now online and responding!")
            print("=" * 60)
            print("\nYou can now run: python test_production.py")
            return 0
        else:
            status = "🔄" if "502" in str(result) else "❌"
            print(f"{status} [{timestamp}] Attempt {attempt}/{max_attempts}: {result}")
        
        time.sleep(5)
    
    print("\n⚠️  Deployment check timed out after 5 minutes.")
    print("Please check Railway dashboard for deployment logs.")
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")
        sys.exit(0)
