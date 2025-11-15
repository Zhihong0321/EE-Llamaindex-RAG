"""Run all end-to-end tests for production readiness verification.

This script runs all E2E tests in sequence and provides a comprehensive
report on the system's production readiness.
"""

import sys
import time
from datetime import datetime


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def run_test(test_name, test_module):
    """Run a single test and return success status."""
    print_header(f"Running: {test_name}")
    
    try:
        # Import and run the test
        module = __import__(test_module, fromlist=[''])
        test_func = getattr(module, [name for name in dir(module) if name.startswith('test_')][0])
        
        start_time = time.time()
        result = test_func()
        elapsed = time.time() - start_time
        
        print(f"\n✅ {test_name} PASSED ({elapsed:.2f}s)")
        return True, elapsed
        
    except Exception as e:
        print(f"\n❌ {test_name} FAILED")
        print(f"   Error: {e}")
        return False, 0


def main():
    """Run all E2E tests."""
    print_header("END-TO-END PRODUCTION READINESS TESTS")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define all tests
    tests = [
        ("Full RAG Workflow", "test_full_workflow"),
        ("Multi-Turn Conversation", "test_multi_turn_conversation"),
        ("Session Isolation", "test_session_isolation"),
        ("Source Retrieval Accuracy", "test_source_accuracy"),
    ]
    
    results = []
    total_time = 0
    
    # Run each test
    for test_name, test_module in tests:
        success, elapsed = run_test(test_name, test_module)
        results.append((test_name, success, elapsed))
        total_time += elapsed
        
        if not success:
            print(f"\n⚠️  Continuing with remaining tests...")
        
        # Small delay between tests
        time.sleep(1)
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Total Time: {total_time:.2f}s")
    
    print("\nDetailed Results:")
    for test_name, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name} ({elapsed:.2f}s)")
    
    # Production readiness assessment
    print_header("PRODUCTION READINESS ASSESSMENT")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ System is PRODUCTION READY")
        print("\nThe RAG API has successfully passed all end-to-end tests:")
        print("  ✅ Full workflow (ingest → chat → retrieve)")
        print("  ✅ Multi-turn conversations with context")
        print("  ✅ Session isolation and security")
        print("  ✅ Source retrieval accuracy")
        print("\nYou can proceed with production deployment.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print(f"\n❌ System is NOT production ready ({failed} test(s) failed)")
        print("\nPlease review the failed tests above and fix the issues before deployment.")
        print("\nFailed tests:")
        for test_name, success, _ in results:
            if not success:
                print(f"  ❌ {test_name}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
