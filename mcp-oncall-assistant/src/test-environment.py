#!/usr/bin/env python3
"""
Simple test script for MCP Oncall Assistant
Tests all major components without running the full server

Usage:
    python src/tools/test-environment.py
    
Location: src/tools/test-environment.py (moved from src/)
"""
import os
import sys
from pathlib import Path

# Add the parent directory (src/) to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_environment():
    """Test the Python environment and imports"""
    print("🧪 Testing Python Environment")
    print("=" * 40)
    
    # Test Python version
    print(f"✅ Python: {sys.version.split()[0]}")
    print(f"✅ Python executable: {sys.executable}")
    print(f"✅ Current directory: {os.getcwd()}")
    print()
    
    # Test required imports
    print("🔍 Testing Required Modules:")
    
    modules_to_test = [
        ("jira", "JIRA"),
        ("mcp.server.fastmcp", "FastMCP"),
        ("dotenv", "python-dotenv"),
        ("pathlib", "pathlib"),
        ("logging", "logging"),
        ("httpx", "httpx")
    ]
    
    failed_imports = []
    
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name}: {e}")
            failed_imports.append(display_name)
    
    if failed_imports:
        print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
        print("Run 'pip install -r requirements.txt' to install missing packages")
        return False
    
    print("\n✅ All required modules imported successfully!")
    return True

def test_environment_variables():
    """Test environment variable loading"""
    print("\n🔧 Testing Environment Variables")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        
        # Load .env from project root (two levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded .env from: {env_file}")
        else:
            print(f"⚠️  .env file not found at: {env_file}")
            load_dotenv()  # Try to load from current directory
        
        env_vars = {
            "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL"),
            "JIRA_EMAIL": os.getenv("JIRA_EMAIL"), 
            "JIRA_TOKEN": os.getenv("JIRA_TOKEN"),
        }
        
        missing_vars = []
        
        for var_name, var_value in env_vars.items():
            if var_value:
                # Hide sensitive values
                display_value = var_value if "TOKEN" not in var_name else "***HIDDEN***"
                print(f"  ✅ {var_name}: {display_value}")
            else:
                print(f"  ⚠️  {var_name}: Not set")
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("Update your .env file with the missing values")
            return False
        
        print("\n✅ All environment variables configured!")
        return True
        
    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        return False

def test_jira_connection():
    """Test JIRA connection (without actually connecting)"""
    print("\n🔗 Testing JIRA Configuration")
    print("=" * 40)
    
    try:
        from jira import JIRA
        from dotenv import load_dotenv
        
        # Load .env from project root
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        load_dotenv(env_file)
        
        jira_url = os.getenv("JIRA_BASE_URL")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_TOKEN")
        
        if not all([jira_url, jira_email, jira_token]):
            print("❌ JIRA credentials not fully configured in .env file")
            return False
        
        # Validate URL format
        if not jira_url.startswith(("http://", "https://")):
            print(f"❌ Invalid JIRA URL format: {jira_url}")
            print("URL should start with http:// or https://")
            return False
        
        # Validate email format
        if "@" not in jira_email:
            print(f"❌ Invalid email format: {jira_email}")
            return False
        
        print(f"✅ JIRA URL: {jira_url}")
        print(f"✅ JIRA Email: {jira_email}")
        print("✅ JIRA Token: ***CONFIGURED***")
        print("\n✅ JIRA configuration looks good!")
        print("Note: Actual connection not tested (use start-mcp.ps1 for full test)")
        return True
        
    except Exception as e:
        print(f"❌ JIRA test failed: {e}")
        return False

def test_mcp_server():
    """Test MCP server creation"""
    print("\n🚀 Testing MCP Server Creation")
    print("=" * 40)
    
    try:
        from mcp.server.fastmcp import FastMCP
        
        # Try to create a test server
        test_server = FastMCP("Test Server")
        print("✅ FastMCP server created successfully")
        
        # Test adding a simple resource
        @test_server.resource("test://hello")
        def test_resource() -> str:
            return "Hello from test resource!"
        
        print("✅ Test resource added successfully")
        
        # Test adding a simple prompt
        @test_server.prompt()
        def test_prompt(message: str = "Hello") -> str:
            return f"Test prompt: {message}"
        
        print("✅ Test prompt added successfully")
        print("\n✅ MCP server components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def test_file_structure():
    """Test required files and directories"""
    print("\n📁 Testing File Structure")
    print("=" * 40)
    
    # Get project root (three levels up from this file: tools/ -> src/ -> project/)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)  # Change to project root for relative path checking
    
    print(f"Project root: {project_root}")
    
    required_files = [
        "src/server.py",
        "requirements.txt",
        ".env"
    ]
    
    optional_files = [
        "README.md",
        "pyproject.toml",
        "uv.lock"
    ]
    
    required_dirs = [
        ".venv"
    ]
    
    missing_required = []
    
    # Check required files
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (REQUIRED)")
            missing_required.append(file_name)
    
    # Check optional files
    for file_name in optional_files:
        if Path(file_name).exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ⚠️  {file_name} (optional)")
    
    # Check required directories
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (REQUIRED)")
            missing_required.append(dir_name)
    
    if missing_required:
        print(f"\n❌ Missing required files/directories: {', '.join(missing_required)}")
        return False
    
    print("\n✅ File structure looks good!")
    return True

def test_server_import():
    """Test importing the main server module"""
    print("\n📦 Testing Server Module Import")
    print("=" * 40)
    
    try:
        # Test importing the server module
        import server
        print("✅ Server module imported successfully")
        
        # Test if main MCP tools are available
        if hasattr(server, 'wplog_find_bottlenecks'):
            print("✅ wplog_find_bottlenecks function found")
        else:
            print("⚠️  wplog_find_bottlenecks function not found")
        
        if hasattr(server, 'initialize_jira'):
            print("✅ initialize_jira function found")
        else:
            print("⚠️  initialize_jira function not found")
        
        print("\n✅ Server module components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Server import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 MCP Oncall Assistant - Environment Test")
    print("=" * 50)
    print(f"📍 Test location: {Path(__file__).relative_to(Path.cwd())}")
    print()
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Environment", test_environment),
        ("Environment Variables", test_environment_variables),
        ("JIRA Configuration", test_jira_connection),
        ("MCP Server", test_mcp_server),
        ("Server Module", test_server_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} test failed!")
        except Exception as e:
            print(f"\n💥 {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your environment is ready!")
        print("\nNext steps:")
        print("1. Run: .\\start-mcp.ps1 -Mode dev")
        print("2. Configure Claude Desktop with your MCP server")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Run: .\\setup-environment.ps1")
        print("2. Update your .env file with JIRA credentials")
        print("3. Make sure you're in the correct directory")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)