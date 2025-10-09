# AI-Enhanced Incident Response MCP Server

An MCP (Model Context Protocol) server built with Python that provides AI-enhanced incident response capabilities, including JIRA integration, CaseWare file repair, and intelligent knowledge base search.

## Features

- 🤖 **AI-Powered Response Suggestions** - Get intelligent recommendations for incident resolution
- 🎫 **JIRA Integration** - Seamless ticket management and tracking
- 🔧 **CaseWare File Repair** - Automated detection and repair of corrupted CaseWare archive files
- 🔍 **Knowledge Base Search** - Intelligent search across help documentation and technical resources
- 📊 **WPLog Diagnostic Analysis** - AI-powered analysis of CaseWare Working Papers log files

## Requirements

- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **[uv](https://docs.astral.sh/uv/)** - Python project manager (recommended):
  - **macOS via Homebrew**:
    ```bash
    brew install uv
    ```
  - **Windows via WinGet**:
    ```bash
    winget install --id=astral-sh.uv -e
    ```
  - **Alternative installation** (any platform):
    ```bash
    # Windows (PowerShell)
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **[Visual Studio Code](https://code.visualstudio.com/)** or another code editor
- **For testing in Claude**:
  - [Claude.ai account](https://claude.ai) (MCP support is available for all account types)
  - [Claude Desktop app](https://claude.ai/download), available for macOS and Windows
- **Git** (optional) - For cloning the repository

## Project Structure

```
mcp-oncall-assistant/
├── scripts/              # 🔧 Automation & Launch Scripts
│   ├── start-mcp.bat        # Windows batch launcher
│   ├── start-mcp.ps1        # PowerShell launcher  
│   ├── setup-environment.ps1  # Full environment setup
│   └── fix-venv.bat         # Virtual environment repair
├── src/                  # 🐍 Python Source Code
│   ├── server.py            # Main MCP server
│   ├── test-environment.py  # Environment validation
│   └── main.py              # Additional entry point
├── .vscode/              # 🛠️ VS Code Configuration
├── .env                  # 🔐 Environment variables
├── requirements.txt      # 📦 Dependencies
└── pyproject.toml        # 🏗️ Project config
```

## Development Setup

### Method 1: Using UV (Recommended)

This project uses `uv` for dependency management and virtual environment handling.

1. **Navigate to the project directory:**
   ```bash
   cd "Caseware Hackathon/2025/mcp-oncall-assistant"
   ```

2. **Set up the uv environment:**
   ```bash
   uv sync
   ```

   This will automatically:
   - Create a virtual environment in `.venv`
   - Install all dependencies from `pyproject.toml` and `uv.lock`

3. **Activate the virtual environment:**

   **Windows (PowerShell):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

   **Note:** To deactivate the virtual environment:
   ```bash
   deactivate
   ```

4. **Set the VS Code Python environment:**

   1. Open the Command Palette: `Shift + Ctrl/Cmd + P`
   2. Select "Python: Select Interpreter"
   3. Choose the `.venv` environment from your project directory
   4. Verify the Python path shows: `./Caseware Hackathon/2025/mcp-oncall-assistant/.venv/Scripts/python.exe` (Windows) or `./Caseware Hackathon/2025/mcp-oncall-assistant/.venv/bin/python` (macOS/Linux)

### Method 2: Manual Setup (Alternative)

If you prefer not to use `uv` or need more control:

1. **Navigate to the project directory:**
   ```bash
   cd "Caseware Hackathon/2025/mcp-oncall-assistant"
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment:**

   **Windows (PowerShell):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   **Windows (CMD):**
   ```cmd
   .\.venv\Scripts\activate.bat
   ```

   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Environment Configuration

1. **Create a `.env` file** in the project root:
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables** in `.env`:
   ```env
   # JIRA Configuration
   JIRA_BASE_URL=https://yourcompany.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_TOKEN=your-jira-api-token

   # Server Configuration
   REQUIRE_HUMAN_APPROVAL=true
   MAX_FILE_SIZE_GB=20
   ALLOWED_EXTENSIONS=.ac,.ac_,.log,.txt,.md
   TOOLS_DIR=./tools
   ```

3. **Get your JIRA API Token:**
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Click "Create API token"
   - Copy the token to your `.env` file

## Running the Server

### Quick Start with Scripts

**Windows users can use the provided automation scripts:**

1. **Test environment and run server:**
   ```bash
   # Test everything first
   scripts\start-mcp.bat test
   
   # Start development server with MCP Inspector
   scripts\start-mcp.bat dev
   
   # Or use PowerShell
   scripts\start-mcp.ps1 test
   scripts\start-mcp.ps1 dev
   ```

### Development Mode

1. **Test the server locally using uv:**

   ```bash
   uv run mcp dev src/server.py
   ```

   This command will:
   - Automatically activate the virtual environment
   - Run the MCP development server with Inspector
   - Show server output and any errors

2. **Alternative: Activate environment first, then run:**

   ```bash
   # Activate virtual environment
   source .venv/bin/activate  # macOS/Linux
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   
   # Run with MCP Inspector (for debugging)
   mcp dev src/server.py
   
   # Or run directly
   python src/server.py
   ```

3. **Using uv run for other commands:**

   ```bash
   # Run any Python command in the uv environment
   uv run python -c "import jira; print('jira works!')"
   
   # Install additional packages
   uv add requests beautifulsoup4
   ```

## Claude Desktop Integration

### Step 1: Find Paths

1. **Find your UV path** (if using UV):

   Windows (PowerShell):
   ```powershell
   where.exe uv
   ```

   MacOS / Linux:
   ```bash
   which uv
   ```

2. **Get absolute path to your server:**

   **Windows:**
   ```powershell
   Get-ChildItem "Caseware Hackathon/2025/mcp-oncall-assistant/server.py" | Select-Object FullName
   ```

   **macOS/Linux:**
   ```bash
   pwd
   # Shows: /path/to/your/My-playgroud
   # Full server path: /path/to/your/My-playgroud/Caseware Hackathon/2025/mcp-oncall-assistant/src/server.py
   ```

### Step 2: Configure Claude Desktop

1. **Open Claude Desktop Configuration:**

   From Claude Desktop:
   - Open Claude Desktop
   - Go to Settings (gear icon)
   - Select "Developer"
   - Click "Edit Config"

   Or manually open the file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add your server configuration:**

   Using UV:
   ```json
   {
     "mcpServers": {
       "incident-response": {
         "command": "/path/to/uv",
         "args": [
           "run",
           "--directory",
           "/path/to/your/My-playgroud/Caseware Hackathon/2025/mcp-oncall-assistant",
           "mcp",
           "run",
           "src/server.py"
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

   Using standard Python:
   ```json
   {
     "mcpServers": {
       "incident-response": {
         "command": "/path/to/your/My-playgroud/Caseware Hackathon/2025/mcp-oncall-assistant/.venv/bin/python",
         "args": [
           "/path/to/your/My-playgroud/Caseware Hackathon/2025/mcp-oncall-assistant/src/server.py"
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

   **Note for Windows users**: Use backslashes in paths:
   - UV: `C:\\path\\to\\uv.exe`
   - Python: `C:\\path\\to\\your\\My-playgroud\\Caseware Hackathon\\2025\\mcp-oncall-assistant\\.venv\\Scripts\\python.exe`
   - Server: `C:\\path\\to\\your\\My-playgroud\\Caseware Hackathon\\2025\\mcp-oncall-assistant\\src\\server.py`

3. **Restart Claude Desktop** completely (quit and reopen)

4. **Test the integration** by asking Claude about incident response capabilities

## License

This project is licensed under the MIT License.