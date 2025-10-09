# 🚀 Quick Start Guide

This guide will get you up and running with the MCP Oncall Assistant in just a few minutes!

## 📋 Prerequisites

- ✅ **Python 3.8+** installed
- ✅ **PowerShell** (comes with Windows)
- ✅ **VS Code** (recommended)

## 🎯 One-Time Setup (5 minutes)

### Step 1: Set up the environment
```powershell
# Run this once to set up everything
.\setup-environment.ps1
```

This script will:
- Create a virtual environment
- Install all required packages (MCP, JIRA, FastMCP, etc.)
- Create VS Code configuration files
- Generate a sample `.env` file

### Step 2: Configure JIRA credentials
Edit the `.env` file and add your JIRA details:

```env
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_TOKEN=your-jira-api-token
```

**Get your JIRA API token:**
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the token to your `.env` file

## ⚡ Daily Usage (30 seconds)

### Test everything is working
```powershell
.\start-mcp.ps1 -Mode test
```

### Start development server
```powershell
.\start-mcp.ps1 -Mode dev
```

### Start production server
```powershell
.\start-mcp.ps1 -Mode run
```

## 🔧 Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup-environment.ps1` | One-time setup | `.\setup-environment.ps1` |
| `start-mcp.ps1` | Start the MCP server | `.\start-mcp.ps1 -Mode dev` |
| `test-environment.py` | Test environment | `python test-environment.py` |

## 🎛️ Script Options

### setup-environment.ps1
```powershell
# Normal setup
.\setup-environment.ps1

# Reset and recreate everything
.\setup-environment.ps1 -Reset
```

### start-mcp.ps1
```powershell
# Development mode (with MCP inspector)
.\start-mcp.ps1 -Mode dev

# Production mode
.\start-mcp.ps1 -Mode run

# Test mode (verify everything works)
.\start-mcp.ps1 -Mode test
```

## 🔍 Troubleshooting

### Problem: "Script execution is disabled"
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: "Virtual environment not found"
**Solution:**
```powershell
.\setup-environment.ps1
```

### Problem: "Missing packages"
**Solution:**
```powershell
.\setup-environment.ps1 -Reset
```

### Problem: "JIRA connection failed"
**Solution:**
1. Check your `.env` file has correct credentials
2. Verify your JIRA URL (should be `https://yourcompany.atlassian.net`)
3. Generate a new API token if needed

### Problem: "Port 6277 is in use"
**Solution:**
The start script automatically kills existing MCP processes, but if needed:
```powershell
Get-Process -Name "mcp" | Stop-Process -Force
```

## 🔗 Claude Desktop Integration

After your server is running, configure Claude Desktop:

### 1. Find your UV path (if using UV)
```powershell
where.exe uv
```

### 2. Edit Claude Desktop config
- **Location**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Content**:
```json
{
  "mcpServers": {
    "incident-response": {
      "command": "/path/to/your/mcp-oncall-assistant/.venv/Scripts/python.exe",
      "args": [
        "/path/to/your/mcp-oncall-assistant/server.py"
      ],
      "env": {
        "JIRA_BASE_URL": "https://yourcompany.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com",
        "JIRA_TOKEN": "your-jira-api-token"
      }
    }
  }
}
```

### 3. Restart Claude Desktop completely

## ⭐ VS Code Integration

The setup script automatically configures VS Code:
- ✅ **Python interpreter** set to your virtual environment
- ✅ **Debug configuration** ready to use
- ✅ **Environment variables** loaded automatically

### Debug in VS Code:
1. Open the project in VS Code
2. Press `F5` or go to Run & Debug
3. Select "Debug MCP Server"

## 📊 Quick Health Check

Run this anytime to verify everything is working:
```powershell
.\start-mcp.ps1 -Mode test
```

This will show:
- ✅ Python environment status
- ✅ Required packages installed
- ✅ JIRA configuration valid
- ✅ MCP server can start
- ✅ All files present

## 🎉 Success!

When everything is working, you should see:
```
🎉 All tests passed! Your environment is ready!
```

You're now ready to use the MCP Oncall Assistant! 🚀

---

## 💡 Pro Tips

- **Always use the scripts** - they handle environment activation automatically
- **Test first** - run `.\start-mcp.ps1 -Mode test` before starting development
- **Check logs** - if something fails, the scripts show detailed error messages
- **Reset if stuck** - `.\setup-environment.ps1 -Reset` fixes most environment issues