# Test Data Directory

This directory contains test files for the MCP On-Call Assistant tools.

## Purpose

Place your test files here to be used by the test scripts without hardcoding absolute paths.

## File Organization

```
test_data/
├── README.md           # This file
├── wplog2014.txt      # Sample WPLog file (not included in repo)
└── sample.ac_         # Sample CaseWare file (not included in repo)
```

## Usage with Test Scripts

All test scripts now support flexible file path configuration:

### Method 1: Command Line Argument (Recommended)
```powershell
# Test wplog bottleneck analysis
python test_wplog_bottlenecks.py "D:\Your\Path\wplog2014.txt"

# Final validation
python final_wplog_validation.py "D:\Your\Path\wplog2014.txt"
```

### Method 2: Environment Variable
```powershell
# Set environment variable (PowerShell)
$env:WPLOG_TEST_FILE = "D:\Your\Path\wplog2014.txt"

# Run tests
python test_wplog_bottlenecks.py
python final_wplog_validation.py
```

```bash
# Set environment variable (Bash)
export WPLOG_TEST_FILE="/path/to/wplog2014.txt"

# Run tests
python test_wplog_bottlenecks.py
python final_wplog_validation.py
```

### Method 3: Default Location
Place your test files in this directory:
```
test_data/wplog2014.txt
```

Then run tests without arguments:
```powershell
python test_wplog_bottlenecks.py
python final_wplog_validation.py
```

## File Requirements

### WPLog Files (wplog2014.txt)
- Format: CaseWare Working Papers log file
- Content: Timestamped log entries
- Size: Any size supported (tested with 12K+ lines)
- Location: Obtain from your CaseWare Working Papers installation

### CaseWare Archive Files (.ac_)
- Format: CaseWare archive/backup files
- Content: OLE compound document structure
- Size: Any size supported
- Location: Created by CaseWare Working Papers

## Privacy Note

⚠️ **Do not commit actual client files to the repository!**

Test files may contain sensitive client information. The `.gitignore` file is configured to exclude:
- `*.txt` (log files)
- `*.ac_` (archive files)
- `*.ac2` (active files)

Only commit sanitized/anonymized test data if needed for documentation purposes.

## Creating Test Data

If you need to share test cases, create minimal synthetic test files:

```python
# Example: Create minimal WPLog test file
with open('test_data/minimal_wplog.txt', 'w') as f:
    f.write('[2014-01-01 10:00:00.000] [INFO] Application started\n')
    f.write('[2014-01-01 10:00:05.000] [INFO] Processing file\n')
    f.write('[2014-01-01 10:01:00.000] [WARN] Operation delayed\n')
```

## Support

For issues with test scripts, see:
- Main README: `../README.md`
- Quick Start Guide: `../docs/QUICK_START_DEMO.md`
- Demo Guide: `../docs/DEMO_GUIDE.md`
