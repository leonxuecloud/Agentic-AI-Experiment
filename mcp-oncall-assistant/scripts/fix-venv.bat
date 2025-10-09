@echo off
:: Emergency fix script for virtual environment issues
echo.
echo ===================================
echo  Virtual Environment Fix Script
echo ===================================
echo.

cd /d "%~dp0"

echo 🗑️  Removing corrupted virtual environment...
if exist ".venv" (
    rmdir /s /q .venv
    echo ✅ Old virtual environment removed
)

echo 🔧 Creating fresh virtual environment...
python -m venv .venv --upgrade-deps
if errorlevel 1 (
    echo ❌ Failed with --upgrade-deps, trying basic creation...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo Make sure Python is properly installed
        pause
        exit /b 1
    )
)

echo ✅ Virtual environment created

echo 🔧 Ensuring pip is available...
.venv\Scripts\python.exe -m ensurepip --upgrade
if errorlevel 1 (
    echo ⚠️  ensurepip failed, but continuing...
)

echo 📦 Installing packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo ✅ Virtual environment fixed!
echo You can now run start-mcp.bat
echo.
pause