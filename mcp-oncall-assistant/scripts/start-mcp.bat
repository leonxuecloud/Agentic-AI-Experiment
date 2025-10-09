@echo off
:: Quick setup and start script for MCP Oncall Assistant
:: This avoids PowerShell execution policy issues

echo.
echo =================================
echo  MCP Oncall Assistant Launcher
echo =================================
echo.

:: Show current directory and Python info
echo 📍 Current directory: %CD%
echo 🐍 Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

:: Store script directory and change to project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
echo 📍 Project directory: %CD%

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo Creating virtual environment...
    python -m venv .venv --upgrade-deps
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment with --upgrade-deps
        echo Trying without --upgrade-deps...
        python -m venv .venv
        if errorlevel 1 (
            echo ❌ Failed to create virtual environment
            pause
            exit /b 1
        )
    )
    echo ✅ Virtual environment created
)

:: Ensure pip is available in virtual environment
echo 🔧 Ensuring pip is available...
.venv\Scripts\python.exe -m ensurepip --upgrade 2>nul
if errorlevel 1 (
    echo ⚠️  ensurepip failed, trying alternative method...
    .venv\Scripts\python.exe -m ensurepip 2>nul
    if errorlevel 1 (
        echo ❌ Failed to install pip in virtual environment
        echo Recreating virtual environment...
        rmdir /s /q .venv
        python -m venv .venv --upgrade-deps
        if errorlevel 1 (
            echo ❌ Failed to recreate virtual environment
            pause
            exit /b 1
        )
        echo ✅ Virtual environment recreated
    )
)

:: Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo Trying alternative activation method...
    call .venv\Scripts\activate
    if errorlevel 1 (
        echo ❌ Virtual environment activation failed completely
        pause
        exit /b 1
    )
)
echo ✅ Virtual environment activated

:: Check if packages are installed
echo 🔍 Checking packages...
.venv\Scripts\python.exe -c "import jira; from mcp.server.fastmcp import FastMCP; import dotenv; import httpx" 2>nul
if errorlevel 1 (
    echo 📦 Installing required packages...
    
    :: First ensure pip is working
    .venv\Scripts\python.exe -m pip --version 2>nul
    if errorlevel 1 (
        echo ❌ pip not available, installing pip...
        .venv\Scripts\python.exe -m ensurepip --upgrade
        if errorlevel 1 (
            echo ❌ Failed to install pip
            pause
            exit /b 1
        )
    )
    
    :: Upgrade pip first
    echo 🔄 Upgrading pip...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    if errorlevel 1 (
        echo ⚠️  Pip upgrade failed, continuing with current version...
    )
    
    :: Install packages
    echo 📥 Installing packages from requirements.txt...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install packages from requirements.txt
        echo 🔄 Trying individual package installation...
        .venv\Scripts\python.exe -m pip install mcp fastmcp jira python-dotenv httpx
        if errorlevel 1 (
            echo ❌ Failed to install packages
            pause
            exit /b 1
        )
    )
    echo ✅ Packages installed
) else (
    echo ✅ All packages available
)

:: Check if .env exists
if not exist ".env" (
    echo 📄 Creating sample .env file...
    echo # JIRA Configuration > .env
    echo JIRA_BASE_URL=https://yourcompany.atlassian.net >> .env
    echo JIRA_EMAIL=your-email@company.com >> .env
    echo JIRA_TOKEN=your-jira-api-token >> .env
    echo. >> .env
    echo # Server Configuration >> .env
    echo REQUIRE_HUMAN_APPROVAL=true >> .env
    echo MAX_FILE_SIZE_GB=20 >> .env
    echo ALLOWED_EXTENSIONS=.ac,.ac_,.log,.txt,.md >> .env
    echo TOOLS_DIR=./tools >> .env
    echo ✅ Sample .env file created
    echo ⚠️  Remember to update .env with your JIRA credentials!
)

:: Ask user what to do
echo.
echo What would you like to do?
echo 1. Test environment
echo 2. Start development server
echo 3. Start production server
echo 4. Exit
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto test
if "%choice%"=="2" goto dev
if "%choice%"=="3" goto run
if "%choice%"=="4" goto end

:test
echo.
echo 🧪 Testing environment...
if exist src\test-environment.py (
    .venv\Scripts\python.exe src\test-environment.py
    if errorlevel 1 (
        echo ❌ Environment test failed
    ) else (
        echo ✅ Environment test completed
    )
) else (
    echo ❌ src\test-environment.py not found
)
echo.
echo Press any key to continue...
pause >nul
goto end

:dev
echo.
echo 🔧 Starting development server...
echo This will open the MCP Inspector
echo Press Ctrl+C to stop the server
echo.
echo Starting MCP development server...
.venv\Scripts\mcp.exe dev "%CD%\src\server.py"
if errorlevel 1 (
    echo.
    echo ❌ Development server failed to start
    echo Trying alternative command...
    .venv\Scripts\python.exe "%CD%\src\server.py"
)
goto end

:run
echo.
echo 🚀 Starting production server...
echo Press Ctrl+C to stop the server
echo.
.venv\Scripts\python.exe "%CD%\src\server.py"
goto end

:end
echo.
echo Goodbye! 👋