#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Environment setup script for MCP Oncall Assistant

.DESCRIPTION
    This script automatically:
    - Creates a virtual environment
    - Installs all required dependencies
    - Creates a sample .env file
    - Configures VS Code settings
    
.PARAMETER Reset
    If specified, removes existing virtual environment and recreates it
    
.EXAMPLE
    .\setup-environment.ps1
    .\setup-environment.ps1 -Reset
#>

param(
    [switch]$Reset
)

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = $ScriptDir

Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow

# Change to project directory
Set-Location $ProjectDir

# Check if Python is available
try {
    $PythonVersion = & python --version 2>&1
    Write-Host "✅ Found Python: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Remove existing virtual environment if Reset is specified
if ($Reset -and (Test-Path ".venv")) {
    Write-Host "🧹 Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".venv"
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "🔨 Creating virtual environment..." -ForegroundColor Cyan
    & python -m venv .venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
Write-Host "" 
$pythonCheck = & python -c "import sys; print(sys.version.split()[0])"
Write-Host "✅ Python: $pythonCheck"
$jiraCheck = & python -c "import sys; import jira; print('✅ JIRA module')" 2>$null
if ($jiraCheck) { Write-Host $jiraCheck }
else { Write-Host "❌ JIRA module" }
$fastmcpCheck = & python -c "from mcp.server.fastmcp import FastMCP; print('✅ FastMCP module')" 2>$null
if ($fastmcpCheck) { Write-Host $fastmcpCheck }
else { Write-Host "❌ FastMCP module" }
 $dotenvCheck = & python -c "import dotenv; print('✅ python-dotenv module')" 2>$null
if ($dotenvCheck) { Write-Host $dotenvCheck }
else { Write-Host "❌ python-dotenv module" }
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📄 Creating sample .env file..." -ForegroundColor Cyan
    
    $EnvContent = @"
# JIRA Configuration
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_TOKEN=your-jira-api-token

# Server Configuration
REQUIRE_HUMAN_APPROVAL=true
MAX_FILE_SIZE_GB=20
ALLOWED_EXTENSIONS=.ac,.ac_,.log,.txt,.md
TOOLS_DIR=./tools
CASEWARE_TOOLS_PATH=./tools/caseware
WPLOG_TOOLS_PATH=./tools/wplog
"@
    
    $EnvContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Sample .env file created" -ForegroundColor Green
    Write-Host "⚠️  Remember to update .env with your actual JIRA credentials!" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Create VS Code workspace settings
Write-Host "⚙️  Creating VS Code workspace settings..." -ForegroundColor Cyan

# Create .vscode directory if it doesn't exist
if (-not (Test-Path ".vscode")) {
    New-Item -ItemType Directory -Path ".vscode" | Out-Null
}

# Get the absolute path to the Python executable
$PythonPath = & python -c "import sys; print(sys.executable.replace('\\', '/'))"

$VSCodeSettings = @{
    "python.pythonPath" = $PythonPath
    "python.defaultInterpreterPath" = $PythonPath
    "python.terminal.activateEnvironment" = $true
    "python.terminal.activateEnvInCurrentTerminal" = $true
    "files.associations" = @{
        "*.env" = "dotenv"
    }
    "python.linting.enabled" = $true
    "python.linting.pylintEnabled" = $false
    "python.linting.flake8Enabled" = $true
    "python.formatting.provider" = "black"
} | ConvertTo-Json -Depth 10

$VSCodeSettings | Out-File -FilePath ".vscode\settings.json" -Encoding UTF8
Write-Host "✅ VS Code settings configured" -ForegroundColor Green

# Create a launch configuration for debugging
$LaunchConfig = @{
    "version" = "0.2.0"
    "configurations" = @(
        @{
            "name" = "Debug MCP Server"
            "type" = "python"
            "request" = "launch"
            "program" = "${workspaceFolder}/src/server.py"
            "console" = "integratedTerminal"
            "cwd" = "${workspaceFolder}"
            "env" = @{
                "PYTHONPATH" = "${workspaceFolder}"
            }
            "envFile" = "${workspaceFolder}/.env"
        }
    )
} | ConvertTo-Json -Depth 10

$LaunchConfig | Out-File -FilePath ".vscode\launch.json" -Encoding UTF8
Write-Host "✅ VS Code debug configuration created" -ForegroundColor Green

# Test the installation
Write-Host "🧪 Testing installation..." -ForegroundColor Cyan
Write-Host ""

# Test imports
& python -c "
import sys
print(f'✅ Python: {sys.version.split()[0]}')

try:
    import jira
    print('✅ JIRA module')
except Exception as e:
    print(f'❌ JIRA module: {e}')

try:
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP module')
except Exception as e:
    print(f'❌ FastMCP module: {e}')

try:
    import dotenv
    print('✅ python-dotenv module')
except Exception as e:
    print(f'❌ python-dotenv module: {e}')
"

Write-Host ""
## Removed final completion and next steps messages as requested