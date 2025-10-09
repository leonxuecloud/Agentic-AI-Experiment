# MCP Oncall Assistant Tools

This directory contains various tools and utilities for the MCP Oncall Assistant project.

## 📁 Directory Structure

```text
src/tools/
├── test-environment.py    # Environment testing script
├── wpfile/               # CaseWare file analysis tools
│   ├── caseware_universal_extractor.py
│   ├── caseware_stream_extractor.py
│   ├── valide_forensic_analyzer.py
│   ├── enhanced_valide_extractor.py
│   └── deep_valide_analyzer.py
└── wplog/               # Working Papers log analysis tools
    ├── wplog_analyzer.py
    └── main.py
```

## 🧪 test-environment.py

**Purpose**: Comprehensive environment validation script for the MCP Oncall Assistant

**Usage**:

```powershell
# From project root
python src/tools/test-environment.py
```

**What it tests**:

- ✅ **File Structure** - Validates all required files and directories exist
- ✅ **Python Environment** - Checks Python version and required module imports
- ✅ **Environment Variables** - Validates JIRA credentials in .env file
- ✅ **JIRA Configuration** - Tests JIRA URL and email format validation
- ✅ **MCP Server** - Tests FastMCP framework functionality
- ✅ **Server Module** - Validates main server.py module imports

**When to use**:

- Before deploying the MCP server
- After environment setup or changes
- When troubleshooting configuration issues
- As part of CI/CD validation

**Features**:

- 🔧 Smart path resolution (works from any location)
- 🔒 Secure credential handling (hides sensitive tokens)
- 📊 Detailed test results with pass/fail status
- 🎯 Actionable error messages and solutions

## 📁 wpfile/ - CaseWare File Tools

Tools for analyzing and extracting data from CaseWare .ac_ archive files:

- **`valide_forensic_analyzer.py`** - Main forensic analysis tool
- **`caseware_universal_extractor.py`** - Universal file extraction
- **`caseware_stream_extractor.py`** - Streaming extraction for large files
- **`enhanced_valide_extractor.py`** - Enhanced extraction with metadata
- **`deep_valide_analyzer.py`** - Deep analysis capabilities

## 📁 wplog/ - Working Papers Log Tools

Tools for analyzing CaseWare Working Papers log files:

- **`wplog_analyzer.py`** - Main log analysis engine
- **`main.py`** - CLI interface for log analysis

These tools provide bottleneck detection, error analysis, timeline generation, and performance reporting.

## 🚀 Integration

All tools in this directory are integrated into the main MCP server (`src/server.py`) and can be called as MCP tools from Claude Desktop or other MCP clients.

For more information, see the main project [README.md](../../README.md).