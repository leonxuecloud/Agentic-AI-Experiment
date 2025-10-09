#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Easy startup script for MCP Oncall Assistant

.DESCRIPTION
    This script auto        & $PythonExe -m mcp dev src\server.py
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Development server failed to start. Trying alternative..." -ForegroundColor Yellow
            & $PythonExe src\server.pycally:
    - Navigates to the correct directory
    - Activates the virtual environment
    - Starts the MCP server
    
.PARAMETER Mode
    dev - Run in development mode with MCP inspector
    run - Run the server directly
    test - Test the environment and connections
    
.EXAMPLE
    .\start-mcp.ps1 -Mode dev
    .\start-mcp.ps1 -Mode test
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "run", "test")]
    [string]$Mode = "dev"
)

# Get the script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "🚀 MCP Oncall Assistant Startup Script" -ForegroundColor Green
Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow

# Change to project directory
Set-Location $ProjectDir

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    
    # Create virtual environment
    & python -m venv .venv --upgrade-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Failed with --upgrade-deps, trying basic creation..." -ForegroundColor Yellow
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    }
    
    # Ensure pip is available
    Write-Host "🔧 Installing pip..." -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe -m ensurepip --upgrade
    
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment (set environment variables manually)
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
$env:VIRTUAL_ENV = Resolve-Path ".venv"
$env:PATH = "$(Resolve-Path '.venv\Scripts');$env:PATH"

# Check if server.py exists
if (-not (Test-Path "src\server.py")) {
    Write-Host "❌ src\server.py not found!" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check required packages
Write-Host "🔍 Checking required packages..." -ForegroundColor Cyan
$PythonExe = ".\.venv\Scripts\python.exe"

try {
    $TestResult = & $PythonExe -c "import jira; from mcp.server.fastmcp import FastMCP; import dotenv; import httpx; print('All packages OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ All required packages available" -ForegroundColor Green
    } else {
        throw "Package import failed"
    }
} catch {
    Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
    
    # Ensure pip is working
    & $PythonExe -m pip --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "🔧 Installing pip..." -ForegroundColor Cyan
        & $PythonExe -m ensurepip --upgrade
    }
    
    # Install packages
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install packages" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Packages installed successfully" -ForegroundColor Green
}

# Check environment file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "You may need to create .env with JIRA credentials" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file found" -ForegroundColor Green
}

# Execute based on mode
switch ($Mode) {
    "dev" {
        Write-Host "🔧 Starting MCP server in development mode..." -ForegroundColor Cyan
        Write-Host "This will open the MCP Inspector for debugging" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        # Change to src directory to avoid path issues with spaces
        Push-Location (Join-Path $ProjectDir "src")
        try {
            # Start MCP dev server from src directory
            $McpExe = Join-Path $ProjectDir ".venv\Scripts\mcp.exe"
            & $McpExe dev server.py
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Development server failed, trying direct server..." -ForegroundColor Yellow
                $PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
                & $PythonExe server.py
            }
        }
        finally {
            Pop-Location
        }
    }
    
    "run" {
        Write-Host "🚀 Starting MCP server..." -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        # Change to src directory to avoid path issues with spaces
        Push-Location (Join-Path $ProjectDir "src")
        try {
            $PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
            & $PythonExe server.py
        }
        finally {
            Pop-Location
        }
    }
    
    "test" {
        Write-Host "🧪 Testing environment..." -ForegroundColor Cyan
        Write-Host ""
        
        # Test Python environment
        Write-Host "Python Version:" -ForegroundColor Yellow
        & $PythonExe --version
        
        Write-Host "`nPython Path:" -ForegroundColor Yellow
        & $PythonExe -c "import sys; print(sys.executable)"
        
        Write-Host "`nCurrent Directory:" -ForegroundColor Yellow
        Get-Location
        
        Write-Host "`nJIRA Test:" -ForegroundColor Yellow
        & $PythonExe -c @"
try:
    from jira import JIRA
    print('✅ JIRA module imported successfully')
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    jira_url = os.getenv('JIRA_BASE_URL')
    if jira_url:
        print(f'✅ JIRA_BASE_URL configured: {jira_url}')
    else:
        print('⚠️  JIRA_BASE_URL not set in .env')
        
except Exception as e:
    print(f'❌ JIRA test failed: {e}')
"@
        
        Write-Host "`nMCP Test:" -ForegroundColor Yellow
        & $PythonExe -c @"
try:
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP imported successfully')
    
    # Test server creation
    mcp = FastMCP('Test Server')
    print('✅ FastMCP server created successfully')
    
except Exception as e:
    print(f'❌ MCP test failed: {e}')
"@
        
        Write-Host "`n✅ Environment test completed!" -ForegroundColor Green
    }
}