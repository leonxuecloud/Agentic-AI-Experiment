#!/usr/bin/env python3
"""
Comprehensive Test Runner for MCP On-Call Assistant

This script runs all tests in the tests directory and provides a comprehensive report.

Usage:
    python tests/run_all_tests.py [path_to_wplog_file]
    
    If no path is provided, uses WPLOG_TEST_FILE environment variable
    or defaults to './test_data/wplog2014.txt'
"""

import sys
import os
from pathlib import Path
import traceback
from datetime import datetime
import subprocess

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

class TestRunner:
    """Comprehensive test runner for all MCP tests"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            start = datetime.now()
            result = test_func()
            end = datetime.now()
            duration = (end - start).total_seconds()
            
            self.results.append({
                'test': test_name,
                'status': 'PASSED' if result else 'FAILED',
                'duration': duration,
                'error': None
            })
            
            print(f"\n[OK] {test_name}: PASSED ({duration:.2f}s)")
            return True
            
        except Exception as e:
            end = datetime.now()
            duration = (end - start).total_seconds()
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            self.results.append({
                'test': test_name,
                'status': 'ERROR',
                'duration': duration,
                'error': error_msg
            })
            
            print(f"\n[X] {test_name}: ERROR ({duration:.2f}s)")
            print(f"  Error: {error_msg}")
            traceback.print_exc()
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print(f"\n\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        total_duration = sum(r['duration'] for r in self.results)
        
        print(f"Total Tests:    {total}")
        print(f"Passed:         {passed} [OK]")
        print(f"Failed:         {failed} [X]")
        print(f"Errors:         {errors} [!]")
        print(f"Total Duration: {total_duration:.2f}s")
        print()
        
        # Detailed results
        print("Detailed Results:")
        print("-" * 60)
        for result in self.results:
            status_symbol = {
                'PASSED': '[OK]',
                'FAILED': '[X]',
                'ERROR': '[!]'
            }.get(result['status'], '?')
            
            print(f"{status_symbol} {result['test']:<40} {result['duration']:>6.2f}s  {result['status']}")
            if result['error']:
                print(f"  └─ {result['error']}")
        
        print()
        
        # Overall status
        if passed == total:
            print("[SUCCESS] ALL TESTS PASSED!")
            return 0
        else:
            print(f"[!] {failed + errors} TEST(S) FAILED OR HAD ERRORS")
            return 1

def get_test_file_path():
    """Get the test file path from arguments, environment, or default"""
    # Priority: 1) Command line arg, 2) Environment variable, 3) Default
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    env_path = os.getenv('WPLOG_TEST_FILE')
    if env_path:
        return env_path
    
    # Default to a test_data directory in the project
    default_path = PROJECT_ROOT / "test_data" / "wplog2014.txt"
    return str(default_path)

# Test functions
def test_path_configuration():
    """Test path configuration logic"""
    test_path = get_test_file_path()
    print(f"Test file path: {test_path}")
    
    # Verify path resolution works
    if len(sys.argv) > 1:
        assert test_path == sys.argv[1], "Command line argument not used"
        print("[OK] Command line argument resolution works")
    elif os.getenv('WPLOG_TEST_FILE'):
        assert test_path == os.getenv('WPLOG_TEST_FILE'), "Environment variable not used"
        print("[OK] Environment variable resolution works")
    else:
        expected = str(PROJECT_ROOT / "test_data" / "wplog2014.txt")
        assert test_path == expected, f"Default path incorrect: {test_path} != {expected}"
        print("[OK] Default path resolution works")
    
    return True

def test_server_imports():
    """Test that server module can be imported"""
    try:
        from server import (
            wplog_find_bottlenecks,
            caseware_analyze_file,
            wplog_analyze_file,
            wplog_analyze_errors
        )
        print("[OK] All server functions imported successfully")
        print(f"  - wplog_find_bottlenecks: {wplog_find_bottlenecks.__name__}")
        print(f"  - caseware_analyze_file: {caseware_analyze_file.__name__}")
        print(f"  - wplog_analyze_file: {wplog_analyze_file.__name__}")
        print(f"  - wplog_analyze_errors: {wplog_analyze_errors.__name__}")
        return True
    except ImportError as e:
        print(f"[X] Import error: {e}")
        return False

def test_tool_imports():
    """Test that tool modules can be imported"""
    try:
        from tools.wplog.wplog_analyzer import WPLogAnalyzer
        print("[OK] WPLogAnalyzer imported successfully")
        
        # Test basic instantiation
        analyzer = WPLogAnalyzer(verbose=False)
        print(f"  - Created analyzer instance: {type(analyzer).__name__}")
        return True
    except ImportError as e:
        print(f"[X] Import error: {e}")
        return False

def test_caseware_fix():
    """Test CaseWare file analysis with temporary file"""
    import tempfile
    from server import caseware_analyze_file
    
    # Create a temporary test file with OLE header
    ole_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'TESTDATA' * 100
    
    with tempfile.NamedTemporaryFile(suffix='.ac_', delete=False) as temp_file:
        temp_file.write(ole_header)
        temp_file.flush()
        temp_path = temp_file.name
        
    try:
        print(f"Testing with temporary file: {temp_path}")
        result = caseware_analyze_file(temp_path)
        
        print(f"[OK] Analysis completed")
        print(f"  - Success: {result.get('success')}")
        print(f"  - File Type: {result.get('file_type')}")
        print(f"  - File Size: {result.get('file_size')} bytes")
        
        assert result.get('success'), "Analysis should succeed"
        assert result.get('file_type') is not None, "File type should be detected"
        
        return True
    finally:
        # Clean up
        try:
            Path(temp_path).unlink()
        except OSError:
            pass

def test_wplog_bottlenecks_with_nonexistent_file():
    """Test wplog_find_bottlenecks error handling with non-existent file"""
    from server import wplog_find_bottlenecks
    
    result = wplog_find_bottlenecks("non_existent_file.txt")
    
    print(f"[OK] Error handling works")
    print(f"  - Success: {result.get('success')}")
    print(f"  - Error message: {result.get('error', 'N/A')}")
    
    assert result.get('success') == False, "Should return success=False for missing file"
    assert 'error' in result, "Should include error message"
    
    return True

def test_wplog_bottlenecks_with_real_file():
    """Test wplog_find_bottlenecks with actual test file (if available)"""
    from server import wplog_find_bottlenecks
    
    test_file = get_test_file_path()
    
    if not Path(test_file).exists():
        print(f"[!] Test file not found: {test_file}")
        print("  Skipping real file test (this is OK for basic validation)")
        return True
    
    print(f"Testing with real file: {test_file}")
    result = wplog_find_bottlenecks(test_file, min_gap_seconds=5.0)
    
    print(f"[OK] Analysis completed")
    print(f"  - Success: {result.get('success')}")
    print(f"  - Total gaps found: {result.get('total_gaps_found', 0)}")
    print(f"  - Top time gaps: {len(result.get('top_time_gaps', []))}")
    
    assert result.get('success') == True, "Analysis should succeed"
    assert 'log_file' in result, "Should include log_file path"
    assert 'top_time_gaps' in result, "Should include top_time_gaps"
    
    return True

def test_environment_setup():
    """Test that the Python environment is properly configured"""
    try:
        import mcp
        import fastmcp
        import httpx
        import jira
        
        print("[OK] All required packages are installed")
        
        # Some modules may not have __version__ attribute
        try:
            print(f"  - mcp: {mcp.__version__ if hasattr(mcp, '__version__') else 'installed'}")
        except AttributeError:
            print("  - mcp: installed")
            
        print(f"  - fastmcp version: {fastmcp.__version__}")
        print(f"  - httpx version: {httpx.__version__}")
        print("  - jira: installed")
        
        # Check Python version
        py_version = sys.version_info
        print(f"  - Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
        
        assert py_version >= (3, 12), "Python 3.12+ required"
        
        return True
    except ImportError as e:
        print(f"[X] Package import error: {e}")
        return False

def test_environment_script():
    """Run tests/test-environment.py as a subprocess and check exit code"""
    env_test_path = Path(__file__).parent / "test-environment.py"
    if not env_test_path.exists():
        print(f"[X] Environment test script not found: {env_test_path}")
        return False
    print(f"Running environment test script: {env_test_path}")
    result = subprocess.run([sys.executable, str(env_test_path)], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("[OK] Environment test script passed")
        return True
    else:
        print(f"[X] Environment test script failed (exit code {result.returncode})")
        print(result.stderr)
        return False

def main():
    """Main test runner"""
    print("="*60)
    print("MCP ON-CALL ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Test File: {get_test_file_path()}")
    print(f"Python Version: {sys.version}")
    print()
    
    runner = TestRunner()
    runner.start_time = datetime.now()
    
    # By default, only run basic tests. The full environment test script runs all checks.
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Path Configuration", test_path_configuration),
        ("Server Module Imports", test_server_imports),
        ("Tool Module Imports", test_tool_imports),
        ("CaseWare Analysis (Temp File)", test_caseware_fix),
        ("WPLog Bottlenecks - Error Handling", test_wplog_bottlenecks_with_nonexistent_file),
        ("WPLog Bottlenecks - Real File", test_wplog_bottlenecks_with_real_file),
    ]

    # Only run the full environment test script if specifically requested
    if os.getenv('RUN_FULL_ENV_TEST', '0') == '1' or '--full-env' in sys.argv:
        tests.append(("Full Environment Test Script", test_environment_script))
    
    for test_name, test_func in tests:
        runner.run_test(test_name, test_func)
    
    runner.end_time = datetime.now()
    
    # Print summary
    exit_code = runner.print_summary()
    
    print(f"\nTest run completed at: {runner.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {(runner.end_time - runner.start_time).total_seconds():.2f}s")
    
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[X] Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
