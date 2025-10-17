# Tests Directory

This directory contains all test scripts for the MCP On-Call Assistant.

## Quick Start

### Run All Tests
```powershell
# Basic test run
python tests/run_all_tests.py

# With specific test file
python tests/run_all_tests.py "D:\Your\Path\wplog2014.txt"

# With environment variable
$env:WPLOG_TEST_FILE = "D:\Your\Path\wplog2014.txt"
python tests/run_all_tests.py
```

## Test Files

### Core Test Scripts

1. **`run_all_tests.py`** - Comprehensive test runner
   - Runs all tests in sequence
   - Provides detailed results and timing
   - Returns exit code 0 on success, 1 on failure

2. **`test_wplog_bottlenecks.py`** - WPLog bottleneck analysis tests
   - Tests with default parameters (5.0s threshold)
   - Tests with sensitive detection (1.0s threshold)
   - Error handling validation
   - Detailed analysis with WPLogAnalyzer

3. **`final_wplog_validation.py`** - Production readiness validation
   - Response structure validation
   - Data quality checks
   - Performance metrics
   - Complete success/failure reporting

4. **`test_caseware_fix.py`** - CaseWare file analysis tests
   - Creates temporary test file with OLE header
   - Tests file analysis functionality
   - Validates OLE structure detection

5. **`test_server.py`** - Server module tests
   - Tests server initialization
   - Validates tool registration
   - Checks server configuration

6. **`test_path_config.py`** - Path configuration verification
   - Tests command line argument resolution
   - Tests environment variable resolution
   - Tests default path resolution

7. **`wplog_analysis_report.py`** - Analysis report generator
   - Generates comprehensive functionality report
   - Provides optimization recommendations
   - Compares to original WPLog Analyser

## Test Organization

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── run_all_tests.py              # Comprehensive test runner
├── test_wplog_bottlenecks.py     # WPLog bottleneck tests
├── final_wplog_validation.py     # Final validation tests
├── test_caseware_fix.py          # CaseWare analysis tests
├── test_server.py                # Server module tests
├── test_path_config.py           # Path configuration tests
└── wplog_analysis_report.py      # Report generator
```

## Running Individual Tests

### WPLog Bottleneck Tests
```powershell
python tests/test_wplog_bottlenecks.py "D:\Path\wplog2014.txt"
```

### Final Validation
```powershell
python tests/final_wplog_validation.py "D:\Path\wplog2014.txt"
```

### Path Configuration Test
```powershell
python tests/test_path_config.py "D:\Path\test.txt"
```

### CaseWare Fix Test
```powershell
python tests/test_caseware_fix.py
```

### Analysis Report
```powershell
python tests/wplog_analysis_report.py
```

## Test Configuration

All tests support three configuration methods:

### 1. Command Line Argument (Recommended)
```powershell
python tests/test_name.py "D:\Your\Path\file.txt"
```

### 2. Environment Variable
```powershell
$env:WPLOG_TEST_FILE = "D:\Your\Path\file.txt"
python tests/test_name.py
```

### 3. Default Location
```powershell
# Place file at: test_data/wplog2014.txt
python tests/test_name.py
```

## Test Results

The comprehensive test runner provides:

- **Total Tests**: Number of tests executed
- **Passed**: Tests that completed successfully ✓
- **Failed**: Tests that failed assertions ✗
- **Errors**: Tests that raised exceptions ⚠
- **Duration**: Time taken for each test and total

Example output:
```
============================================================
TEST SUMMARY
============================================================

Total Tests:    7
Passed:         7 ✓
Failed:         0 ✗
Errors:         0 ⚠
Total Duration: 3.45s

Detailed Results:
------------------------------------------------------------
✓ Environment Setup                          0.12s  PASSED
✓ Path Configuration                         0.01s  PASSED
✓ Server Module Imports                      0.23s  PASSED
✓ Tool Module Imports                        0.15s  PASSED
✓ CaseWare Analysis (Temp File)              0.45s  PASSED
✓ WPLog Bottlenecks - Error Handling         0.18s  PASSED
✓ WPLog Bottlenecks - Real File              2.31s  PASSED

🎉 ALL TESTS PASSED!
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_all_tests.py
```

### Azure Pipelines Example
```yaml
trigger:
- main

pool:
  vmImage: 'windows-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'
- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  displayName: 'Install dependencies'
- script: python tests/run_all_tests.py
  displayName: 'Run tests'
```

## Test Development

### Adding New Tests

1. Create test file in `tests/` directory
2. Add shebang and docstring
3. Implement test functions
4. Add to `run_all_tests.py` if needed

Example template:
```python
#!/usr/bin/env python3
"""
Test description

Usage:
    python tests/test_new_feature.py [arguments]
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_feature():
    """Test the new feature"""
    # Test implementation
    assert True, "Test condition"
    return True

if __name__ == "__main__":
    try:
        result = test_feature()
        if result:
            print("✓ Test passed!")
            sys.exit(0)
        else:
            print("✗ Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

## Best Practices

### 1. Use Assertions
```python
assert result is not None, "Result should not be None"
assert len(items) > 0, "Should have at least one item"
```

### 2. Provide Clear Output
```python
print(f"✓ Test completed successfully")
print(f"  - Items processed: {count}")
print(f"  - Duration: {duration:.2f}s")
```

### 3. Handle Errors Gracefully
```python
try:
    result = dangerous_operation()
except Exception as e:
    print(f"✗ Operation failed: {e}")
    return False
```

### 4. Clean Up Resources
```python
try:
    temp_file = create_temp_file()
    # Test with temp_file
finally:
    Path(temp_file).unlink()
```

### 5. Test Both Success and Failure Cases
```python
# Test success case
result = function_with_valid_input()
assert result['success'] == True

# Test failure case
result = function_with_invalid_input()
assert result['success'] == False
assert 'error' in result
```

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'server'
```
**Solution**: Ensure you're running from project root or update `sys.path`

### File Not Found
```
❌ Test file not found: test_data/wplog2014.txt
```
**Solution**: Provide file path via command line or environment variable

### Unicode Errors (Windows)
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution**: Set environment variable before running tests
```powershell
$env:PYTHONIOENCODING = "utf-8"
python tests/run_all_tests.py
```

### Permission Errors
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Close files/programs using test files, or run with elevated permissions

## Related Documentation

- **Testing Guide**: `../docs/TESTING_GUIDE.md`
- **Test Data**: `../test_data/README.md`
- **Setup Guide**: `../docs/SETUP_GUIDE.md`
- **Main README**: `../README.md`

## Summary

✅ **Comprehensive test coverage** - All major features tested  
✅ **Flexible configuration** - Multiple ways to specify test data  
✅ **CI/CD ready** - Easy to integrate with automation  
✅ **Well organized** - All tests in one location  
✅ **Clear reporting** - Detailed results and timing  
✅ **Production ready** - Validates deployment readiness
