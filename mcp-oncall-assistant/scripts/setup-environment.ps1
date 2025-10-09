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

Write-Host "🔧 MCP Oncall Assistant Environment Setup" -ForegroundColor Green
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
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Cyan
& python -m pip install --upgrade pip

# Install or upgrade requirements
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan

$RequiredPackages = @(
    "mcp[cli]>=1.0.0",
    "fastmcp>=2.2.3",
    "jira>=3.8.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.24.0"
)

foreach ($Package in $RequiredPackages) {
    Write-Host "  Installing $Package..." -ForegroundColor Yellow
    & pip install $Package
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $Package installed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed to install $Package" -ForegroundColor Red
    }
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
Write-Host "🎉 Environment setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update .env file with your JIRA credentials" -ForegroundColor White
Write-Host "2. Run: .\start-mcp.ps1 -Mode test" -ForegroundColor White
Write-Host "3. Run: .\start-mcp.ps1 -Mode dev" -ForegroundColor White
Write-Host ""
Write-Host "For JIRA API token, visit:" -ForegroundColor Yellow
Write-Host "https://id.atlassian.com/manage-profile/security/api-tokens" -ForegroundColor Cyan