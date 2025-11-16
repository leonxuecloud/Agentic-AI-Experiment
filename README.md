# Agentic AI Experiment 🤖

Welcome to the **Agentic AI Experiment** repository! This workspace explores cutting-edge **Agentic AI systems**—intelligent automation that exhibits autonomy, adaptability, and decision-making capabilities for real-world operational challenges.

We're building production-ready **MCP (Model Context Protocol) servers** that seamlessly bridge AI models with enterprise workflows, incident response, and diagnostic automation.

---

## 🎯 What's Inside

This repository hosts **two complementary MCP server implementations**, each designed for different user personas:

| Project | Language | Target Users | Focus | Status |
|---------|----------|--------------|-------|--------|
| **[mcp-oncall-assistant](#python-mcp-oncall-assistant)** | Python 3.12+ | 👨‍💻 Developers & DevOps | File forensics & diagnostics | ✅ Production |
| **[oncall-support](#typescript-oncall-support-server)** | TypeScript 5+ | 🎧 Support Teams | Multi-platform incident triage (JIRA + New Relic + GitHub) | ✅ Production |

---

## 🐍 Python: MCP On-Call Assistant

**For Developers: Advanced file analysis, forensics, and diagnostic automation**

### Target Audience
**Developers and DevOps engineers** who need deep technical diagnostics, file repair capabilities, and forensic analysis of CaseWare Working Papers files.

### Core Capabilities

- 🔧 **CaseWare File Repair** — Multi-strategy extraction and validation of corrupted Working Papers archives
- 📊 **WPLog Diagnostic Analysis** — AI-powered log analysis with bottleneck detection
- 🔍 **Forensic File Analysis** — Deep inspection using multiple extraction algorithms
- 🤖 **AI-Enhanced Diagnostics** — Pattern recognition and root cause identification
- 🎫 **JIRA Integration** — Read-only ticket management for developer workflows

### Technology Stack

```
Python 3.12+ | FastMCP 2.2+ | UV Package Manager | HTTPX | Python-dotenv
```

### Quick Start

```bash
# Clone and navigate
git clone https://github.com/leonxuecloud/Agentic-AI-Experiment.git
cd Agentic-AI-Experiment/mcp-oncall-assistant

# Install UV (if needed)
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and test
uv sync
cp .env.example .env
# Edit .env with your JIRA credentials

python tests/run_all_tests.py

# Run server
uv run mcp dev src/server.py
```

### Tools Available

| Tool | Description |
|------|-------------|
| `repair_caseware_file` | Multi-strategy archive repair and extraction |
| `analyze_wplog` | Comprehensive Working Papers log analysis |
| `forensic_file_analysis` | Deep corruption analysis and recovery |
| `get_jira_ticket` | Retrieve ticket details with full context |
| `search_jira_tickets` | JQL-based ticket search |

### Project Structure

```
mcp-oncall-assistant/
├── src/
│   ├── server.py              # Main MCP server
│   ├── main.py                # Alternative entry point
│   └── tools/
│       ├── wpfile/            # CaseWare file tools (5 modules)
│       └── wplog/             # Log analysis tools
├── tests/                     # Comprehensive test suite
├── scripts/                   # Automation scripts (Windows)
├── pyproject.toml             # Dependencies & metadata
└── README.md                  # Full documentation
```

📖 **[Full Python Documentation →](mcp-oncall-assistant/README.md)**

---

## 🔷 TypeScript: On-Call Support Server

**For Support Teams: Enterprise-grade incident response with full platform integration**

### Target Audience
**Support personnel and on-call teams** who need to triage tickets, automate incident response workflows, and integrate with multiple monitoring and ticketing platforms.

### Core Capabilities

- 🎫 **Full JIRA Workflow Automation** — Comments, field updates, transitions, metadata queries
- 📊 **New Relic Integration** — Performance monitoring and incident correlation
- 🔗 **GitHub Integration** — Link incidents to code repositories and deployment events
- 🤖 **Enhanced AI Triage** — Automated priority assessment with duplicate detection
- 📋 **Structured Workflow Prompts** — 6 production-ready templates for support teams
- 📁 **Secure File Operations** — Download, extract, list, read with path validation
- 🌐 **Multi-Transport** — STDIO (local) + HTTP (network) + Dual mode
- 🔒 **Enterprise Security** — JWT, CORS, command whitelist, Helmet
- 📊 **Production Monitoring** — Health checks, Prometheus metrics
- 🐳 **Container-Ready** — Docker, Kubernetes, Docker Compose

### Technology Stack

```
TypeScript 5+ | Node.js 18+ | MCP SDK 1.0 | Express | Vitest | Zod | Docker | K8s
Integrations: JIRA API | New Relic API | GitHub API
```

### Quick Start

```bash
# Navigate to project
cd Agentic-AI-Experiment/oncall-support

# Install and configure
npm install
cp env.example .env
# Edit .env with your JIRA credentials

# Build and test
npm run build
npm test                       # 45+ tests

# Run server
npm start                      # STDIO mode (Claude Desktop)
npm run start:http             # HTTP mode (port 3001)
npm run start:dual             # Both transports
```

### Tools Available

| Tool | Type | Description |
|------|------|-------------|
| `get-jira-ticket` | Read | Detailed ticket retrieval with compact mode |
| `search-jira-tickets` | Read | JQL search with result limits |
| `add-jira-comment` | Write | Post comments with visibility control |
| `update-jira-fields` | Write | Update priority, labels, components, custom fields |
| `transition-jira-ticket` | Write | Move tickets through workflow |
| `get-jira-transitions` | Read | List available workflow transitions |
| `get-jira-field-options` | Read | Query field metadata |
| `ticket-analysis` | Analysis | Root cause/impact/timeline analysis |
| `knowledge-search` | Analysis | Similar issues & knowledge lookup |
| `ticket-triage` | Analysis | Enhanced priority assessment |
| `download-file` | File | Secure remote downloads |
| `extract-zip` | File | Archive extraction |
| `list-local-files` | File | File enumeration |
| `read-local-file` | File | Safe content retrieval |

### Prompts Available

| Prompt | Purpose |
|--------|---------|
| `customer-issue` | Structured issue report template |
| `troubleshooting-guide` | Guided investigation steps |
| `customer-communication` | Professional response drafting |
| `escalation-template` | Formal escalation handoff |
| `knowledge-base-article` | KB article scaffold |
| `ticket-triage` | Guided triage script |

### Project Structure

```
oncall-support/
├── src/
│   ├── mcp-server.ts          # Main server
│   ├── tools/
│   │   ├── jira/              # JIRA service (7 tools)
│   │   ├── support-automation/ # Analysis tools (3)
│   │   ├── file-operations/   # File tools (4)
│   │   └── mcp/               # MCP integration
│   ├── prompts/               # 6 workflow templates
│   └── __tests__/             # Vitest test suites
├── k8s/                       # Kubernetes manifests
├── test/                      # Integration tests
├── docker-compose.yml
├── Dockerfile
├── package.json
└── README.md                  # Full documentation
```

📖 **[Full TypeScript Documentation →](oncall-support/README.md)**

---

## 🔄 Feature Comparison

| Feature | Python (mcp-oncall-assistant) | TypeScript (oncall-support) |
|---------|-------------------------------|------------------------------|
| **Target Users** | 👨‍💻 Developers & DevOps | 🎧 Support Teams & On-Call |
| **Best For** | File forensics & diagnostics | Full incident workflow automation |
| **JIRA Operations** | Read-only (developer access) | Read + Write (full support workflow) |
| **Platform Integrations** | JIRA only | 🎯 JIRA + New Relic + GitHub |
| **Primary Focus** | CaseWare file repair & log analysis | Ticket triage & multi-platform incident response |
| **File Operations** | Advanced forensic extraction | Standard download/extract/read |
| **Deployment Modes** | STDIO only | STDIO + HTTP + Dual |
| **Tools Count** | 5 specialized tools | 15 tools (7 JIRA + 3 Analysis + 5 File) |
| **Prompts** | ❌ None | ✅ 6 structured templates |
| **Resources** | ❌ None | ✅ 3 resource types |
| **Testing** | Comprehensive Python tests | 45+ Vitest tests + integration |
| **Container Support** | Basic | Docker + K8s + Compose |
| **Monitoring** | Basic | Health + Prometheus metrics |
| **Security** | Path validation, env isolation | JWT, CORS, whitelist, Helmet |
| **Production Ready** | ✅ Specialized | ✅ Enterprise-grade |

---

## 🔧 Claude Desktop Integration

Both projects can be integrated with Claude Desktop for local AI-powered automation.

### Configuration File Location

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Python Project Configuration

```json
{
  "mcpServers": {
    "mcp-oncall-assistant": {
      "command": "C:\\Users\\YourUsername\\AppData\\Local\\Microsoft\\WinGet\\Links\\uv.exe",
      "args": [
        "run",
        "--directory",
        "C:\\path\\to\\Agentic-AI-Experiment\\mcp-oncall-assistant",
        "mcp",
        "run",
        "src/server.py"
      ]
    }
  }
}
```

**Find UV path**: Run `where.exe uv` (Windows) or `which uv` (macOS/Linux)

### TypeScript Project Configuration

```json
{
  "mcpServers": {
    "oncall-support": {
      "command": "node",
      "args": ["dist/mcp-server.js", "--transport=stdio"],
      "cwd": "C:\\path\\to\\Agentic-AI-Experiment\\oncall-support"
    }
  }
}
```

### Running Both Servers

You can configure both servers simultaneously in Claude Desktop:

```json
{
  "mcpServers": {
    "mcp-oncall-assistant": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-oncall-assistant", "mcp", "run", "src/server.py"]
    },
    "oncall-support": {
      "command": "node",
      "args": ["dist/mcp-server.js", "--transport=stdio"],
      "cwd": "/path/to/oncall-support"
    }
  }
}
```

---

## 🧪 Testing

### Python Project Tests

```bash
cd mcp-oncall-assistant

# Run default test suite
python tests/run_all_tests.py

# Run full environment validation
python tests/run_all_tests.py --full-env

# Run specific tests
python tests/test_caseware_fix.py
python tests/test_wplog_bottlenecks.py
python tests/test_path_config.py
```

### TypeScript Project Tests

```bash
cd oncall-support

# Unit tests
npm test
npm run test:coverage

# Specific test suites
npm run test:error-handling
npm run test:startup
npm run test:integration

# Live JIRA integration tests
node test/jira-integration.test.mjs all
node test/jira-integration.test.mjs triage
node test/jira-integration.test.mjs workflow

# MCP Inspector
npm run inspect:mcp
```

---

## 🐳 Docker Deployment

### Python Project

```bash
cd mcp-oncall-assistant

# Build
docker build -t mcp-oncall-assistant:latest .

# Run
docker run --env-file .env mcp-oncall-assistant:latest
```

### TypeScript Project

```bash
cd oncall-support

# Development with Compose
docker-compose up -d oncall-support-dev

# Production build
docker build -t oncall-support-mcp:latest .
docker run -p 3001:3001 --env-file .env oncall-support-mcp:latest

# Health check
curl http://localhost:3001/health
curl http://localhost:3001/metrics
```

### Kubernetes

```bash
cd oncall-support

# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=oncall-support

# Port forward
kubectl port-forward deploy/oncall-support-mcp 3001:3001
```

---

## 🔒 Security Best Practices

Both projects implement multiple security layers:

### Common Security Features

- ✅ **Environment Isolation** — All secrets in `.env` files, never hard-coded
- ✅ **Token Management** — Secure JIRA API token handling
- ✅ **Graceful Error Handling** — Structured error responses without exposing internals
- ✅ **Path Validation** — Prevention of directory traversal attacks
- ✅ **Minimal Permissions** — Recommend least-privilege JIRA tokens

### TypeScript Project Additional Security

- ✅ **Command Whitelist** — Regex-based allowed commands for execution tool
- ✅ **JWT Authentication** — Optional bearer token auth for HTTP mode
- ✅ **CORS Protection** — Configurable origin restrictions
- ✅ **Helmet Integration** — Security headers automatically applied
- ✅ **Rate Limiting** — Protection against abuse (configurable)
- ✅ **Non-root Container** — Docker runs as unprivileged user

### Recommended JIRA Permissions

| Operation | Required Permission |
|-----------|---------------------|
| Read tickets | Browse Projects, View Issues |
| Add comments | Add Comments |
| Update fields | Edit Issues |
| Transition tickets | Transition Issues |

**Important**: Use dedicated service accounts with scoped permissions, never personal accounts.

---

## 📚 Documentation

### Python Project
- [README.md](mcp-oncall-assistant/README.md) — Complete setup and usage
- [QUICKSTART.md](mcp-oncall-assistant/QUICKSTART.md) — Fast start guide
- [tests/README.md](mcp-oncall-assistant/tests/README.md) — Testing guide

### TypeScript Project
- [README.md](oncall-support/README.md) — Full API reference
- [MCP_INSPECTOR_GUIDE.md](oncall-support/MCP_INSPECTOR_GUIDE.md) — Testing guide
- [docker-compose.yml](oncall-support/docker-compose.yml) — Container setup
- [k8s/deployment.yaml](oncall-support/k8s/deployment.yaml) — K8s manifests

### External Resources
- [Model Context Protocol](https://modelcontextprotocol.io/) — Official MCP docs
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP framework
- [MCP SDK](https://github.com/modelcontextprotocol/sdk) — TypeScript SDK
- [Claude Desktop](https://claude.ai/download) — Desktop app download

---

## 🗺️ Roadmap

### Shared Goals
- [ ] Enhanced AI model integration (multi-provider support)
- [ ] Extended JIRA capabilities (attachments, links, watchers)
- [ ] Performance optimization and caching strategies
- [ ] Unified monitoring and observability platform

### Python Project
- [ ] Additional file format support (beyond CaseWare)
- [ ] ML-based anomaly detection in logs
- [ ] Real-time log streaming analysis
- [ ] HTTP transport mode (network deployment)

### TypeScript Project
- [ ] Webhook processor activation (see `archive/webhook-processor/`)
- [ ] Resource template expansion
- [ ] OpenTelemetry distributed tracing
- [ ] Advanced caching layer (Redis)
- [ ] Rate limiting per-client/per-tool

---

## 🤝 Contributing

We welcome contributions to both projects!

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with tests
4. **Test** thoroughly (see Testing section)
5. **Document** your changes
6. **Commit** with clear messages: `git commit -m 'Add amazing feature'`
7. **Push** to your fork: `git push origin feature/amazing-feature`
8. **Submit** a Pull Request

### Development Standards

**Python Project:**
- Follow PEP 8 style guidelines
- Use Black for formatting
- Use Ruff for linting
- Write pytest tests for new features
- Update type hints (mypy compatible)

**TypeScript Project:**
- Follow TypeScript strict mode
- Use ESLint for code quality
- Write Vitest tests (unit + integration)
- Maintain 80%+ test coverage
- Update JSDoc comments

### Code Review Process

- All PRs require at least one review
- CI tests must pass
- Documentation must be updated
- Security implications must be addressed

---

## 🏆 Production Status

| Criteria | Python Project | TypeScript Project |
|----------|----------------|-------------------|
| **Architecture** | ✅ Modular & extensible | ✅ Enterprise-grade |
| **Test Coverage** | ✅ Comprehensive suite | ✅ 45+ tests |
| **Documentation** | ✅ Complete | ✅ Complete + API docs |
| **Type Safety** | ✅ Type hints | ✅ Strict TypeScript |
| **Error Handling** | ✅ Graceful | ✅ Comprehensive |
| **Security** | ✅ Implemented | ✅ Multi-layer |
| **Monitoring** | ⚠️ Basic | ✅ Full metrics |
| **Container Support** | ✅ Docker | ✅ Docker + K8s + Compose |
| **Multi-Transport** | ⚠️ STDIO only | ✅ STDIO + HTTP + Dual |
| **Production Deploy** | ✅ Ready | ✅ Battle-tested |

---

## 💡 Use Cases

### Python Project Best For:
**Developer & DevOps Use Cases:**
- Diagnosing corrupted CaseWare Working Papers files
- Analyzing WPLog files for performance bottlenecks
- Forensic analysis of file corruption patterns
- Automated file repair workflows
- Deep technical diagnostics requiring specialized tools
- Developer-focused ticket tracking and investigation

### TypeScript Project Best For:
**Support Team & On-Call Use Cases:**
- Automated incident triage and prioritization for support personnel
- Full JIRA workflow automation (comments, transitions, field updates)
- Correlating incidents across JIRA, New Relic, and GitHub
- Multi-user incident response teams (HTTP mode)
- Integration with monitoring platforms (New Relic) and code repos (GitHub)
- Enterprise deployments requiring monitoring and security
- AI-assisted customer communication and escalation drafting
- Support team collaboration and knowledge management

---

## 📄 License

This project is licensed under the **MIT License**.

See individual project directories for specific license details.

---

## 🆘 Support & Community

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/leonxuecloud/Agentic-AI-Experiment/issues)
- **Discussions**: Check existing issues or start a new discussion
- **Documentation**: Refer to project-specific READMEs for detailed guides

### Reporting Bugs

When reporting bugs, please include:
- Project name (Python or TypeScript)
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Node version, etc.)
- Relevant logs or error messages

### Feature Requests

We're always interested in new ideas! Open an issue with:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach (optional)

---

## 🎓 Learning Resources

### MCP Protocol
- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [MCP Server Concepts](https://modelcontextprotocol.io/docs/learn/server-concepts)
- [Building MCP Servers](https://modelcontextprotocol.io/docs/tutorials/building-a-server)

### Tools & Frameworks
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [TypeScript Best Practices](https://www.totaltypescript.com/)
- [Vitest Testing Framework](https://vitest.dev/)

---

## 🌟 Acknowledgments

Built with ❤️ by the Agentic AI Experiment team

**Powered by:**
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — Universal AI-application protocol
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP framework
- [MCP SDK](https://github.com/modelcontextprotocol/sdk) — TypeScript implementation
- [Claude Desktop](https://claude.ai/) — AI assistant integration
- [UV](https://docs.astral.sh/uv/) — Modern Python packaging

---

## 📊 Repository Stats

- **Languages**: Python 3.12+, TypeScript 5+
- **Total Tools**: 20+ (5 Python + 15 TypeScript)
- **Test Coverage**: 45+ automated tests
- **Container Images**: 2 (Python + TypeScript)
- **Supported Platforms**: Windows, macOS, Linux
- **Deployment Options**: Local (STDIO), Network (HTTP), Container (Docker/K8s)

---

**Ready to supercharge your on-call operations with AI?** 🚀

Start with the Python project for advanced diagnostics or the TypeScript project for full incident automation. Both integrate seamlessly with Claude Desktop for AI-powered workflows.

*Agentic AI Experiment — Building the future of intelligent operational automation.*
