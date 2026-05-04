import sys
import os
import subprocess
import glob

def run_regression():
    print("====================================================")
    print("🛡️  YOURBESTPATH FIDUCIARY REGRESSION SUITE v1.0")
    print("====================================================\n")
    
    # 1. Discover all test files
    test_files = glob.glob("tests/**/test_*.py", recursive=True)
    test_files.sort()
    
    print(f"🔎 Discovered {len(test_files)} test scripts.")
    print("🚀 Executing Agent Mesh & Core Library Tests...\n")
    
    passed = 0
    failed = 0
    failures = []
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    
    for test_file in test_files:
        print(f"Running {test_file}...", end=" ", flush=True)
        try:
            # Run the test as a standalone script
            result = subprocess.run(
                [sys.executable, test_file],
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED")
                failed += 1
                failures.append((test_file, result.stderr or result.stdout))
        except Exception as e:
            print(f"⚠️ ERROR: {e}")
            failed += 1
            failures.append((test_file, str(e)))
            
    # 2. Summary Report
    print("\n" + "="*52)
    if failed == 0:
        print(f"✅ REGRESSION PASSED: {passed}/{len(test_files)} tests stable.")
    else:
        print(f"❌ REGRESSION FAILED: {failed} instabilities detected.")
        print("-" * 52)
        for test, error in failures:
            print(f"\nFAILURE in {test}:")
            print(error[:500] + "..." if len(error) > 500 else error)
    print("="*52)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_regression()
