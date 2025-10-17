#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Easy startup script for MCP Oncall Assistant

.DESCRIPTION
        Reliable launcher for the MCP Oncall Assistant server.
        Features:
            - Ensures virtual environment matches the minimum Python version declared in pyproject.toml (requires-python)
            - Creates or rebuilds virtual environment automatically if missing or wrong version
            - Installs required packages
            - Supports development (MCP inspector), run, and test modes
            - Provides optional force rebuild parameter
            - Supports explicit Python path override via PREFERRED_PYTHON environment variable

.PARAMETER Mode
    dev   - Run in development mode with MCP inspector
    run   - Run the server directly
    test  - Test the environment and connections

.PARAMETER ForceRebuild
    When provided (switch), deletes and recreates the virtual environment even if it exists.

.PARAMETER KillVenvProcs
    When provided (switch), attempts to kill processes locking the venv before rebuild.

.PARAMETER PreferHighest
    When provided (switch), rebuilds venv using the highest available Python version if higher than current.

.ENVIRONMENT
    PREFERRED_PYTHON - Path to a specific python.exe to use for venv creation (bypasses py launcher discovery)

.EXAMPLE
    .\start-mcp.ps1 -Mode dev
    .\start-mcp.ps1 -Mode test
    .\start-mcp.ps1 -ForceRebuild -PreferHighest
    $env:PREFERRED_PYTHON = "C:\path\to\python.exe"; .\start-mcp.ps1 -ForceRebuild
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "run", "test")]
    [string]$Mode = "dev",
    [switch]$ForceRebuild,
    [switch]$KillVenvProcs,
    [switch]$PreferHighest
)

# Get the script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "[*] MCP Oncall Assistant Startup Script" -ForegroundColor Green
Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow

# Check for processes that might lock the venv
$lockingProcs = @()
$lockingProcs += Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*Agentic-AI-Experiment\mcp-oncall-assistant\.venv*"
}
$lockingProcs += Get-Process -Name "uv" -ErrorAction SilentlyContinue

if ($lockingProcs.Count -gt 0 -and ($ForceRebuild -or -not (Test-Path ".venv\Scripts\python.exe"))) {
    Write-Host ""
    Write-Host "[!]  WARNING: Found $($lockingProcs.Count) process(es) that might lock the .venv directory" -ForegroundColor Yellow
    Write-Host "This can cause 'Access is denied' errors when trying to rebuild the venv." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recommended: Run the cleanup script first:" -ForegroundColor Cyan
    Write-Host "  .\scripts\cleanup-venv-locks.ps1" -ForegroundColor White
    Write-Host ""
    
    if (-not $KillVenvProcs) {
        $response = Read-Host "Kill these processes automatically now? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            $KillVenvProcs = $true
        }
    }
}

# Change to project directory
Set-Location $ProjectDir

function Get-RequiredPythonSpec {
    # Parse pyproject.toml requires-python (simple regexp; avoids needing a TOML parser dependency here)
    $PyProjectPath = Join-Path $ProjectDir 'pyproject.toml'
    if (-not (Test-Path $PyProjectPath)) { return $null }
    $content = Get-Content $PyProjectPath -Raw
    $match = [regex]::Match($content, 'requires-python\s*=\s*"([^"]+)"')
    if ($match.Success) { return $match.Groups[1].Value } else { return $null }
}

function Get-MinMajorMinorFromSpec {
    param([string]$Spec)
    if (-not $Spec) { return $null }
    # Expect forms like ">=3.12" or ">=3.12,<4.0" etc; take first >= or == version
    $versionMatch = [regex]::Match($Spec, '(?:>=|==)\s*(\d+\.\d+)')
    if ($versionMatch.Success) { return $versionMatch.Groups[1].Value } else { return $null }
}

function Stop-VenvProcesses {
    param([string]$VenvPath)
    if (-not $KillVenvProcs) { return }
    Write-Host "🛑 Attempting to stop processes locking $VenvPath" -ForegroundColor Yellow
    try {
        $pyExe = Join-Path $VenvPath 'Scripts/python.exe'
        Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $pyExe } | ForEach-Object {
            Write-Host "[>] Stopping process $($_.Id) ($($_.ProcessName))" -ForegroundColor Yellow
            try { $_.Kill() } catch {}
        }
        
        # Also kill any UV processes that might be locking the venv
        Get-Process -Name "uv" -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "[>] Stopping UV process $($_.Id)" -ForegroundColor Yellow
            try { $_.Kill() } catch {}
        }
        
        # Wait a moment for processes to fully terminate
        Start-Sleep -Milliseconds 500
    } catch { Write-Host "[!] Process enumeration failed: $($_.Exception.Message)" -ForegroundColor Yellow }
}

function New-PythonVenv {
    param(
        [string]$PythonLauncher,
        [string[]]$PythonLauncherArgs,
        [string]$TargetVersionMajorMinor
    )
    Write-Host "[BUILD] Creating Python virtual environment (target >= $TargetVersionMajorMinor)" -ForegroundColor Yellow
    $existingPath = (Resolve-Path .venv -ErrorAction SilentlyContinue)
    if ($existingPath) {
        Stop-VenvProcesses -VenvPath $existingPath
        
        # Kill any lingering UV processes that might interfere
        Get-Process -Name "uv" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        
        $stamp = (Get-Date -Format 'yyyyMMddHHmmss')
        $backup = ".venv_backup_$stamp"
        Write-Host "[CLEAN] Renaming existing .venv to $backup (safe backup instead of direct delete)" -ForegroundColor Yellow
        try {
            Rename-Item -Path $existingPath -NewName $backup -ErrorAction Stop
            Write-Host "[OK] Backup created: $backup" -ForegroundColor Green
        } catch {
            Write-Host "[X] Failed to rename existing venv: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Attempting direct delete fallback with aggressive retry..." -ForegroundColor Yellow
            
            # Try multiple times with increasing delays
            $retries = 3
            $success = $false
            for ($i = 1; $i -le $retries; $i++) {
                try {
                    Write-Host "Attempt $i of $retries..." -ForegroundColor Yellow
                    
                    # Clear read-only attributes recursively
                    Get-ChildItem -Path $existingPath -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object { 
                        try { 
                            $_.Attributes = 'Normal' 
                        } catch {}
                    }
                    
                    # Try to remove the directory
                    Remove-Item -Recurse -Force $existingPath -ErrorAction Stop
                    Write-Host "[OK] Direct deletion of existing venv succeeded on attempt $i" -ForegroundColor Green
                    $success = $true
                    break
                } catch {
                    if ($i -lt $retries) {
                        Write-Host "[!] Attempt $i failed: $($_.Exception.Message)" -ForegroundColor Yellow
                        Write-Host "Waiting 2 seconds before retry..." -ForegroundColor Yellow
                        Start-Sleep -Seconds 2
                        
                        # Kill processes again
                        Get-Process -Name "uv","python" -ErrorAction SilentlyContinue | Where-Object {
                            $_.Path -like "*$ProjectDir*"
                        } | Stop-Process -Force -ErrorAction SilentlyContinue
                    } else {
                        throw
                    }
                }
            }
            
            if (-not $success) {
                Write-Host "[X] All deletion attempts failed" -ForegroundColor Red
                Write-Host "" -ForegroundColor Yellow
                Write-Host "TROUBLESHOOTING STEPS:" -ForegroundColor Cyan
                Write-Host "1. Close ALL terminals in VS Code" -ForegroundColor Yellow
                Write-Host "2. Close any Python processes or IDEs using this project" -ForegroundColor Yellow
                Write-Host "3. Run this command to kill all related processes:" -ForegroundColor Yellow
                Write-Host "   Get-Process python,uv -ErrorAction SilentlyContinue | Where-Object { `$_.Path -like '*Agentic-AI-Experiment*' } | Stop-Process -Force" -ForegroundColor White
                Write-Host "4. Manually delete the .venv folder using File Explorer" -ForegroundColor Yellow
                Write-Host "5. Try running the script again" -ForegroundColor Yellow
                exit 1
            }
        }
    }
    # Use the dynamically discovered Python launcher to create the virtual environment
    & $PythonLauncher @PythonLauncherArgs -m venv .venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "[X] Failed to create Python virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    if ($backup) {
        # Try async cleanup of backup if we renamed
        Write-Host "[DELETE] Scheduling background removal of $backup" -ForegroundColor Yellow
        Start-Job -ScriptBlock { param($p) if (Test-Path $p) { Remove-Item -Recurse -Force $p } } -ArgumentList $backup | Out-Null
    }
}

# Determine required Python major.minor from pyproject.toml
$RequiresSpec = Get-RequiredPythonSpec
$TargetMajorMinor = Get-MinMajorMinorFromSpec -Spec $RequiresSpec
if (-not $TargetMajorMinor) {
    Write-Host "[!] Could not parse requires-python from pyproject.toml; proceeding without version enforcement" -ForegroundColor Yellow
}

$NeedVenv = $true
$ExistingVersion = $null
if (Test-Path ".venv\Scripts\python.exe") {
    $NeedVenv = $false
    if ($ForceRebuild) {
        Write-Host "[REBUILD] ForceRebuild requested" -ForegroundColor Yellow
        $NeedVenv = $true
    } else {
        $ExistingVersion = & .\.venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[!] Could not determine existing venv Python version; will rebuild" -ForegroundColor Yellow
            $NeedVenv = $true
        }
    }
}

function Convert-Version { param($v); if (-not $v) { return 0 }; $parts = $v -split '\.'; [int]$parts[0]*1000 + [int]$parts[1] }

# Discover highest installed Python via py launcher (Windows only) if requested
$HighestAvailable = $null
if ($PreferHighest -and (Get-Command py -ErrorAction SilentlyContinue)) {
    try {
        # py -0p lists installed versions; parse lines like: -3.12-64 \Path
        $list = py -0p 2>$null
        $versions = @()
        foreach ($line in $list) {
            $m = [regex]::Match($line, '-(\d+\.\d+)')
            if ($m.Success) { $versions += $m.Groups[1].Value }
        }
        if ($versions.Count -gt 0) {
            $HighestAvailable = ($versions | Sort-Object {[int]($_ -split '\.')[0]} , {[int]($_ -split '\.')[1]} -Descending | Select-Object -First 1)
            Write-Host "[INFO] Highest discovered Python via py launcher: $HighestAvailable" -ForegroundColor Cyan
        }
    } catch { Write-Host "[!] Could not enumerate py launcher versions: $($_.Exception.Message)" -ForegroundColor Yellow }
}

if ($ExistingVersion -and $HighestAvailable) {
    if (Convert-Version $ExistingVersion -lt (Convert-Version $HighestAvailable)) {
        Write-Host "[>] Existing venv Python $ExistingVersion is lower than highest available $HighestAvailable; scheduling rebuild." -ForegroundColor Yellow
        $NeedVenv = $true
        $TargetMajorMinor = $HighestAvailable
    } else {
        Write-Host "[OK] Existing venv Python $ExistingVersion already at or above highest available ($HighestAvailable)" -ForegroundColor Green
    }
} elseif ($HighestAvailable -and -not $ExistingVersion) {
    # No existing venv; use highest available if it meets minimum
    if ($TargetMajorMinor -and (Convert-Version $HighestAvailable -lt (Convert-Version $TargetMajorMinor))) {
        Write-Host "[!] Highest available Python $HighestAvailable is below required $TargetMajorMinor" -ForegroundColor Yellow
    } else {
        $TargetMajorMinor = $HighestAvailable
    }
}

if (-not $ExistingVersion -and -not $NeedVenv -and $TargetMajorMinor) {
    Write-Host "[INFO] No existing version info but venv present; assuming compatible." -ForegroundColor Cyan
}

if ($ExistingVersion -and $TargetMajorMinor -and -not $HighestAvailable -and -not $ForceRebuild) {
    $existingVal = Convert-Version $ExistingVersion
    $targetVal = Convert-Version $TargetMajorMinor
    if ($existingVal -lt $targetVal) {
        Write-Host "[!] Existing venv Python $ExistingVersion < required $TargetMajorMinor; rebuilding" -ForegroundColor Yellow
        $NeedVenv = $true
    } elseif (-not $PreferHighest) {
        Write-Host "[OK] Existing venv Python $ExistingVersion meets requirement >= $TargetMajorMinor" -ForegroundColor Green
    }
}

if ($NeedVenv) {
    # Resolve a suitable Python launcher
    $PyCmd = $null
    $PyCmdArgs = @()
    
    # Check for explicit environment override first
    if ($env:PREFERRED_PYTHON -and (Test-Path $env:PREFERRED_PYTHON)) {
        Write-Host "[INFO] Using PREFERRED_PYTHON override: $env:PREFERRED_PYTHON" -ForegroundColor Cyan
        $testVer = & $env:PREFERRED_PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $testVerNum = Convert-Version $testVer
            $targetVerNum = Convert-Version $TargetMajorMinor
            if ($testVerNum -ge $targetVerNum) {
                Write-Host "[OK] PREFERRED_PYTHON version $testVer meets requirement >= $TargetMajorMinor" -ForegroundColor Green
                Write-Host "[BUILD] Creating Python virtual environment with PREFERRED_PYTHON (version $testVer)" -ForegroundColor Yellow
                $PyCmd = $env:PREFERRED_PYTHON
                $PyCmdArgs = @()
            } else {
                Write-Host "[!] PREFERRED_PYTHON version $testVer < required $TargetMajorMinor; will use default discovery" -ForegroundColor Yellow
            }
        } else {
            Write-Host "[!] PREFERRED_PYTHON failed version check; will use default discovery" -ForegroundColor Yellow
        }
    }
    
    # Fall back to py launcher discovery if no override or override failed
    if (-not $PyCmd -and (Get-Command py -ErrorAction SilentlyContinue)) {
        if ($TargetMajorMinor) {
            & py "-$TargetMajorMinor" --version 2>$null
            if ($LASTEXITCODE -eq 0) { $PyCmd = 'py'; $PyCmdArgs = @("-$TargetMajorMinor") }
        }
        if (-not $PyCmd) {
            & py --version 2>$null
            if ($LASTEXITCODE -eq 0) { $PyCmd = 'py'; $PyCmdArgs = @() }
        }
    }
    
    # Final fallback to 'python' in PATH
    if (-not $PyCmd) {
        Write-Host "[INFO] Using fallback 'python' executable; ensure it satisfies >= $TargetMajorMinor" -ForegroundColor Yellow
        $PyCmd = 'python'
        $PyCmdArgs = @()
    }
    
    New-PythonVenv -PythonLauncher $PyCmd -PythonLauncherArgs $PyCmdArgs -TargetVersionMajorMinor $TargetMajorMinor
}

# Activate virtual environment (set environment variables manually)
Write-Host "[+] Activating virtual environment..." -ForegroundColor Cyan
$env:VIRTUAL_ENV = Resolve-Path ".venv"
$env:PATH = "$(Resolve-Path '.venv\Scripts');$env:PATH"

# Check if server.py exists
if (-not (Test-Path "src\server.py")) {
    Write-Host "[X] src\server.py not found!" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "[CHECK] Checking required packages..." -ForegroundColor Cyan
$PythonExe = ".\.venv\Scripts\python.exe"

function Install-Requirements {
    Write-Host "� Installing required packages..." -ForegroundColor Yellow
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Failed to install packages" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Packages installed successfully" -ForegroundColor Green
}

try {
    & $PythonExe -c "import jira; from mcp.server.fastmcp import FastMCP; import dotenv; import httpx; print('All packages OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] All required packages available" -ForegroundColor Green
    } else {
        throw "Package import failed"
    }
} catch {
    # Ensure pip is working
    & $PythonExe -m pip --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[+] Installing pip..." -ForegroundColor Cyan
        & $PythonExe -m ensurepip --upgrade
    }
    Install-Requirements
}

# Verify typer is present (required by mcp[cli])
try {
    & $PythonExe -c "import typer" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Typer CLI dependency available" -ForegroundColor Green
    } else {
        Write-Host "[!] Typer not found; installing mcp[cli] explicitly" -ForegroundColor Yellow
        & $PythonExe -m pip install 'mcp[cli]'
    }
} catch {
    Write-Host "[!] Typer import check encountered an issue: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Check environment file
if (-not (Test-Path ".env")) {
    Write-Host "[!]  .env file not found" -ForegroundColor Yellow
    Write-Host "You may need to create .env with JIRA credentials" -ForegroundColor Yellow
} else {
    Write-Host "[OK] .env file found" -ForegroundColor Green
}

# Execute based on mode
switch ($Mode) {
    "dev" {
        Write-Host "[+] Starting MCP server in development mode..." -ForegroundColor Cyan
        Write-Host "This will open the MCP Inspector for debugging" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        # Change to src directory to avoid path issues with spaces
        Push-Location (Join-Path $ProjectDir "src")
        try {
            # Use mcp.exe but prevent UV from syncing the environment
            $env:UV_NO_SYNC = "1"
            $env:UV_FROZEN = "1"
            $McpExe = Join-Path $ProjectDir ".venv\Scripts\mcp.exe"
            & $McpExe dev server.py
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[X] Development server failed, trying direct server..." -ForegroundColor Yellow
                $PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
                & $PythonExe server.py
            }
        }
        finally {
            Remove-Item Env:\UV_NO_SYNC -ErrorAction SilentlyContinue
            Remove-Item Env:\UV_FROZEN -ErrorAction SilentlyContinue
            Pop-Location
        }
    }
    
    "run" {
        Write-Host "[START] Starting MCP server..." -ForegroundColor Cyan
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
        Write-Host "[TEST] Testing environment..." -ForegroundColor Cyan
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
    print('[OK] JIRA module imported successfully')
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    jira_url = os.getenv('JIRA_BASE_URL')
    if jira_url:
        print(f'[OK] JIRA_BASE_URL configured: {jira_url}')
    else:
        print('[!]  JIRA_BASE_URL not set in .env')
        
except Exception as e:
    print(f'[X] JIRA test failed: {e}')
"@
        
        Write-Host "`nMCP Test:" -ForegroundColor Yellow
        & $PythonExe -c @"
try:
    from mcp.server.fastmcp import FastMCP
    print('[OK] FastMCP imported successfully')
    
    # Test server creation
    mcp = FastMCP('Test Server')
    print('[OK] FastMCP server created successfully')
    
except Exception as e:
    print(f'[X] MCP test failed: {e}')
"@
        
        Write-Host "`n[OK] Environment test completed!" -ForegroundColor Green
    }
}