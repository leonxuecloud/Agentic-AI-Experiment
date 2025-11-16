<!-- ================================================================== -->
# Oncall Support MCP Server
<!-- ================================================================== -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://github.com/leonxuecloud/My-playgroud)

Production-ready Model Context Protocol (MCP) server for oncall support teams. Secure Jira ticket operations, support automation (analysis, knowledge search, triage), and structured prompts in a unified TypeScript architecture.

Transports: STDIO (local) + HTTP (remote). Docker & Kubernetes ready. Minimal, extensible, security‑aware.

---
## Table of Contents
1. Overview
2. Feature Matrix
3. Architecture
4. Quick Start
5. Prerequisites
6. Installation & Scripts
7. Configuration
8. Tools
9. Prompts
10. Workflow Example
11. Transports
12. Security
13. Monitoring
14. Docker / Compose
15. Kubernetes
16. Project Structure
17. Development Workflow
18. Extending (Add Tool / Prompt)
19. Roadmap
20. Contributing
21. License
22. FAQ

---
## 1. Overview
Accelerate incident response with strongly typed tools and reusable prompts. Focused on read‑only Jira access, intelligent ticket analysis, and low‑friction operator workflows.

---
## 2. Feature Matrix
| Category | Capabilities |
|----------|-------------|
| Jira Service | Ticket detail retrieval, JQL search |
| Support Automation | Ticket analysis, knowledge search, triage recommendations |
| File Operations | Safe download, unzip, list and read local files |
| Prompts | 6 structured workflow templates |
| Transports | STDIO + HTTP (+ dual mode) |
| Deployment | Docker, Compose, Kubernetes manifest |
| Monitoring | /health + /metrics (basic Prometheus) |
| Security | Env isolation, command whitelist, path safety, CORS (HTTP) |

---
## 3. Architecture
Core server (`mcp-server.ts`) registers tools & prompts once; transport layer (stdio or Streamable HTTP) is selected at startup.

```
src/
├── mcp-server.ts
├── tools/
│   ├── jira/                # Jira integration tools
│   ├── support-automation/  # Analysis, knowledge, triage
│   └── file-operations/     # Download, extract, list, read
├── prompts/                 # Prompt factories
├── templates/               # Markdown prompt templates
├── auth/                    # (OAuth scaffolding)
├── storage/                 # Simple storage helpers
└── __tests__/               # Vitest suites
```

Dual mode (`--transport=dual`) launches both HTTP and STDIO for mixed clients.

---
## 4. Quick Start
```powershell
git clone https://github.com/leonxuecloud/My-playgroud.git
cd My-playgroud/oncall-support
npm install
Copy-Item env.example .env   # Windows PowerShell
# cp env.example .env        # macOS/Linux
npm run build
npm start                    # STDIO mode for Claude Desktop
# or
npm run start:http           # HTTP mode
```

Claude Desktop config:
```json
{
  "mcpServers": {
    "oncall-support": {
      "command": "node",
      "args": ["dist/mcp-server.js", "--transport=stdio"],
      "cwd": "C:/absolute/path/to/oncall-support"
    }
  }
}
```

---
## 5. Prerequisites
| Item | Notes |
|------|-------|
| Node.js 18+ | Runtime environment |
| Jira API Token | Read‑only access preferred |
| Git | Clone & version control |
| (Optional) Docker | Container build & run |

---
## 6. Installation & Scripts
| Script | Purpose |
|--------|---------|
| build | Compile TypeScript → `dist/` |
| start / start:http / start:dual | Run server in chosen transport |
| dev / dev:http / dev:dual | Hot dev via tsx |
| test / test:* | Vitest suites & coverage |
| lint / lint:fix | ESLint checks |
| type-check | Strict TS type validation |
| clean | Remove build artifacts |
| inspect:mcp | Launch MCP Inspector against HTTP endpoint |

PowerShell examples:
```powershell
npm run dev:http
npm test
npm run inspect:mcp
```

---
## 7. Configuration
Core environment variables (see `env.example`):

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| JIRA_BASE_URL | Jira instance base URL | - | Yes |
| JIRA_USERNAME | Jira account/email | - | Yes |
| JIRA_API_TOKEN | Jira API token | - | Yes |
| ALLOWED_COMMANDS | Regex allowlist for command exec tool | Provided | No |
| MAX_DOWNLOAD_SIZE | Max bytes for file downloads | 104857600 | No |
| LOCAL_STORAGE_DIR | Root for local file tools | ./oncall-files | No |
| MCP_PORT | HTTP server port | 3001 | No |
| CORS_ORIGIN | Allowed origins (comma list) | localhost | No |
| JWT_SECRET | Signing secret (HTTP auth) | - | Recommended |

Minimal `.env` example:
```env
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
LOCAL_STORAGE_DIR=./oncall-files
MCP_PORT=3001
```

### MCP Integration (Optional)
Enable remote Atlassian MCP server metadata (tools & prompts) discovery and local caching.

1. Ensure `mcp.json` exists at project root:
   ```json
   {
     "servers": {
       "atlassian-mcp-server": {
         "url": "https://mcp.atlassian.com/v1/sse",
         "type": "http"
       }
     },
     "inputs": []
   }
   ```
2. Set flag in `.env`:
   ```properties
   ENABLE_MCP_SERVER=true
   ```
3. Use helper `getMcpOverview()` (from `src/tools/mcp/mcp-service.ts`) or call server startup logic to fetch & cache.

Caching:
- Tools → `cache/mcp-tools.json`
- Prompts → `cache/mcp-prompts.json`

Sources reported as: `remote`, `cache`, `missing-config`, `disabled`, or `error`.

If the real server uses SSE only, adjust `mcp-service.ts` to implement an EventSource handshake; current implementation uses placeholder REST endpoints derived from the base URL.


---
## 8. Tools (15 total: 7 Jira + 3 Support + 5 File Ops)

### Jira Tools
| Tool | Type | Purpose |
|------|------|---------|
| get-jira-ticket | Read | Retrieve detailed ticket (fields, comments, changelog) |
| search-jira-tickets | Read | JQL search with controlled result limits |
| **add-jira-comment** | **Write** | **Post comments with visibility control (public/internal team)** |
| **update-jira-fields** | **Write** | **Update priority, labels, components, custom fields** |
| **transition-jira-ticket** | **Write** | **Move tickets through workflow (e.g., New → In Progress)** |
| **get-jira-transitions** | **Read** | **List available workflow transitions for a ticket** |
| **get-jira-field-options** | **Read** | **Query cascading select & enum values before updating** |

### Support Automation Tools
| Tool | Purpose |
|------|---------|
| ticket-analysis | Root cause / impact / timeline synthesis |
| knowledge-search | Similar issues & knowledge lookup |
| ticket-triage | Priority assessment + recommendations |

### File Operation Tools
| Tool | Purpose |
|------|---------|
| download-file | Secure remote file download |
| extract-zip | Unzip previously downloaded archive |
| list-local-files | Enumerate files under storage root |
| read-local-file | Safe file content retrieval |

All are registered in `src/mcp-server.ts`.

---
## 9. Prompts (6)
| Prompt | Purpose |
|--------|---------|
| customer-issue | Structured customer issue report template |
| troubleshooting-guide | Guided investigation steps |
| customer-communication | Draft communication (initial/update/resolution/etc.) |
| escalation-template | Formal escalation handoff |
| knowledge-base-article | KB article scaffold |
| ticket-triage | Guided triage script |

---
## 10. Workflow Example

### Read-Only Analysis
```typescript
const ticket = get-jira-ticket({ ticketId: "PROD-123" });
const analysis = ticket-analysis({
  ticketId: "PROD-123",
  analysisType: "root_cause",
  additionalContext: "Intermittent DB timeouts"
});
const knowledge = knowledge-search({
  topic: "database timeout",
  searchScope: "similar_issues",
  timeframe: "90d"
});
const triage = ticket-triage({ ticketId: "PROD-123", includeRecommendations: true });
```

### Full Triage Workflow (with Write Operations)
```typescript
// 1. Analyze ticket
const triage = ticket-triage({ ticketId: "PROD-123", includeRecommendations: true, enhanced: true });

// 2. Post internal triage comment
add-jira-comment({
  ticketId: "PROD-123",
  body: "🤖 Automated Triage\n\nPriority: Should escalate to High\nReason: Production outage detected\nRecommended labels: outage, backend, critical",
  visibility: { type: "role", value: "Developers" }  // Internal team only
});

// 3. Update fields based on analysis
update-jira-fields({
  ticketId: "PROD-123",
  updates: {
    priority: { name: "High" },
    labels: ["outage", "backend", "critical", "ai-triaged"],
    customFields: {
      "customfield_10218": {  // Component-Area cascading field
        value: "Backend",
        child: { value: "Database" }
      }
    }
  }
});

// 4. Check available transitions
get-jira-transitions({ ticketId: "PROD-123" });

// 5. Move to appropriate state
transition-jira-ticket({
  ticketId: "PROD-123",
  transitionId: "31",  // From get-jira-transitions
  comment: "Moving to In Progress after automated triage"
});
```

---
## 11. Transports
| Mode | Command | Use Case |
|------|---------|----------|
| STDIO | `npm start` | Local desktop (Claude Desktop) |
| HTTP | `npm run start:http` | Remote clients / network integration |
| Dual | `npm run start:dual` | Simultaneous local + network |

Override port: `node dist/mcp-server.js --transport=http --port=3100`

---
## 12. Security

### Jira Operations
* **Write Tools Available**: Field updates, comments, transitions (use with appropriate permissions)
* **Credential Protection**: All auth via env variables (never hard-coded)
* **Graceful Error Handling**: Failed operations return structured error messages
* **Comment Visibility**: Support for public vs. internal team comments

### File & Command Security
* Command execution limited by `ALLOWED_COMMANDS` regex
* Path traversal prevention for local file tools
* Download size limits enforced

### HTTP Mode Security
* Optional JWT + CORS for HTTP mode
* Container user isolation (non‑root user in Dockerfile)

### Best Practices
1. **Jira API Token**: Use restricted token with minimum required permissions; rotate regularly
2. **Review Write Operations**: Test field updates and transitions in non-production first
3. **Comment Visibility**: Always specify visibility for sensitive triage analysis
4. **JWT_SECRET**: Set strong secret in production HTTP deployments
5. **CORS**: Restrict `CORS_ORIGIN` to trusted domains only
6. **Audit Logging**: Monitor Jira audit logs for automated changes

### Permission Recommendations
| Operation | Recommended Jira Permission |
|-----------|----------------------------|
| Read tickets | Browse Projects, View Issues |
| Add comments | Add Comments |
| Update fields | Edit Issues |
| Transition tickets | Transition Issues, Edit Issues |

Use a dedicated service account with minimal scoped permissions.

---
## 13. Monitoring
Health:
```powershell
curl http://localhost:3001/health
```
Metrics (Prometheus exposition):
```powershell
curl http://localhost:3001/metrics
```
Inspector (after starting HTTP server):
```powershell
npx @modelcontextprotocol/inspector http://localhost:3001/mcp
```

---
## 14. Docker / Compose
Build & run locally:
```powershell
docker build -t oncall-support-mcp:latest .
docker run -p 3001:3001 --env-file .env oncall-support-mcp:latest
```
Compose (development):
```powershell
docker-compose up -d oncall-support-dev
```
Stops:
```powershell
docker-compose down
```

---
## 15. Kubernetes
Basic deployment (after image push):
```powershell
kubectl apply -f k8s/deployment.yaml
kubectl get pods -l app=oncall-support
kubectl port-forward deploy/oncall-support-mcp 3001:3001
```
Add ingress, secrets & config maps for production hardening.

---
## 16. Project Structure
```
oncall-support/
├── src/
│   ├── mcp-server.ts                  # Unified server entrypoint
│   ├── tools/                         # Tool categories
│   │   ├── jira/                      # Jira ticket + search tools
│   │   ├── support-automation/        # Analysis, triage, knowledge tools
│   │   └── file-operations/           # download/extract/list/read local files
│   ├── prompts/                       # Prompt factories
│   ├── templates/                     # Markdown + HTML prompt/assets
│   ├── auth/                          # (JWT/OAuth scaffolding)
│   ├── storage/                       # Simple storage helpers
│   └── __tests__/                     # Vitest suites
├── archive/                           # Legacy & prototype artifacts
│   ├── test-runner.ts                 # Comprehensive test script (archived)
│   ├── python-server/                 # Older experimental server impl
│   ├── webhook-processor/             # Future webhook integration scaffold
│   └── old-docs/                      # Historical documentation
├── dist/                              # Build output
├── oncall-files/                      # Local file tool storage root
├── k8s/                               # Kubernetes manifests
├── .mcp-storage/                      # Session/audit storage (runtime)
├── docker-compose.yml
├── Dockerfile
├── env.example
├── env.development
├── env.production
├── package.json
├── package-lock.json
├── tsconfig.json
├── vitest.config.ts
└── README.md
```

---
## 17. Development Workflow
```powershell
npm run dev            # Rapid iteration (stdio)
npm run dev:http       # HTTP dev
npm run build
npm test               # All tests
npm run test:coverage  # Coverage (vitest)
npm run lint && npm run type-check
```
<!-- Legacy duplicated sections pruned below to keep README concise and accurate. -->
export const newTool = {
  name: "new-tool",
  description: "Short description",
  schema: { param: z.string().describe("Parameter description") },
  handler: async ({ param }) => ({
    content: [{ type: "text", text: `Result: ${param}` }]
  })
};
```

Add a Prompt:
```typescript
server.prompt(
  "your-prompt",
  "Prompt description",
  { param: z.string().describe("Parameter") },
  async ({ param }) => ({
    messages: [{ role: "user", content: { type: "text", text: `Template for ${param}` } }]
  })
);
```

---
## Roadmap

| Item | Status |
|------|--------|
| Resources support | Backlog |
| Extended metrics | Backlog |
| Rate limiting | Backlog |
| OpenTelemetry tracing | Backlog |

---
## Contributing
1. Fork & branch (`feature/xyz`)
2. Implement change + tests
3. Run tests
4. Update docs
5. Open Pull Request

---
## License
MIT License – see `LICENSE`.

---
## Production Readiness

| Aspect | Status |
|--------|--------|
| Unified architecture | ✅ |
| Type safety | ✅ |
| Security controls | ✅ |
| Dual transports | ✅ |
| Health & metrics | ✅ |
| Container/K8s | ✅ |
| Documentation | ✅ |

---
## Support
- GitHub Issues (bugs/features)
- MCP Spec: https://modelcontextprotocol.io/

---
**Ready to enhance oncall support with AI?** Start in STDIO mode, expand to HTTP when needed. 🚀
<!-- ================================================================== -->
# Oncall Support MCP Server
<!-- ================================================================== -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://github.com/leonxuecloud/My-playgroud)

<!-- ================================================================== -->
# Oncall Support MCP Server
<!-- ================================================================== -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://github.com/leonxuecloud/My-playgroud)

Production-ready Model Context Protocol (MCP) server for oncall support teams. Delivers secure Jira ticket operations, support automation (analysis, knowledge, triage), and structured prompts via a unified TypeScript architecture.

Transports: STDIO (local desktop) + HTTP (remote/network). Container & Kubernetes ready.

---
## Table of Contents
1. [Overview](#overview)
2. [Feature Matrix](#feature-matrix)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Tools](#tools)
8. [Prompts](#prompts)
9. [Workflow Example](#workflow-example)
10. [Security](#security)
11. [Monitoring](#monitoring)
12. [Project Structure](#project-structure)
13. [Development & Testing](#development--testing)
14. [Extending](#extending)
15. [Roadmap](#roadmap)
16. [Contributing](#contributing)
17. [License](#license)
18. [Production Readiness](#production-readiness)
19. [Support](#support)

---
## Overview

A unified MCP server exposing 5 production tools (2 Jira + 3 Support Automation) and 6 prompts to streamline incident response. Focus: clarity, reliability, security, and extensibility.

---
## Feature Matrix

| Category | Capabilities |
|----------|-------------|
| Jira Service | Get ticket details, JQL search |
| Support Automation | Ticket analysis, knowledge search, automated triage |
| Prompts | 6 structured templates (issue, troubleshooting, communication, escalation, KB article, triage) |
| Transports | STDIO + HTTP (StreamableHTTP) |
| Deployment | Docker + Kubernetes manifest |
| Monitoring | /health + /metrics (Prometheus) |
| Security | Path traversal prevention, env isolation, CORS (HTTP) |

---
## Architecture

Unified service pattern keeps tool logic cohesive:

```
src/tools/
├── jira/
│   ├── jira-service.ts          # Jira API + tool wrappers
│   └── index.ts
└── support-automation/
    ├── support-automation-service.ts  # Analysis, knowledge, triage
    └── index.ts
```

Key components:
- Tools: 5 (get-jira-ticket, search-jira-tickets, ticket-analysis, knowledge-search, ticket-triage)
- Prompts: 6 (customer-issue, troubleshooting-guide, customer-communication, escalation-template, knowledge-base-article, ticket-triage)
- Transports: STDIO + HTTP

---
## Quick Start

```bash
git clone https://github.com/leonxuecloud/My-playgroud.git
cd My-playgroud/oncall-support
npm install
cp env.example .env
npm run build
npm start            # STDIO mode
# or
npm run start:http   # HTTP mode
```

Claude Desktop snippet:
```json
{
  "mcpServers": {
    "oncall-support": {
      "command": "node",
      "args": ["dist/mcp-server.js", "--transport=stdio"],
      "cwd": "C:/absolute/path/to/oncall-support"
    }
  }
}
```

---
## Installation

Prerequisites:
| Requirement | Notes |
|-------------|-------|
| Node.js 18+ | Runtime |
| Jira API Token | Read-only access |

Create env file:
```bash
cp env.example .env
```
Edit `.env`:
```env
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
LOCAL_STORAGE_DIR=./oncall-files
```

Token steps:
1. Atlassian Account → Security → API tokens
2. Create token
3. Set `JIRA_API_TOKEN`

---
## Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| JIRA_BASE_URL | Jira instance URL | - | Yes |
| JIRA_USERNAME | Jira user/email | - | Yes |
| JIRA_API_TOKEN | Jira API token | - | Yes |
| LOCAL_STORAGE_DIR | Local storage root | ./oncall-files | No |
| MCP_PORT | HTTP port | 3001 | No |
| ENABLE_JIRA_COMPACT | Force compact Jira ticket responses if set to `true` | false | No |
| JIRA_COMPACT_MAX_DESCRIPTION_CHARS | Max characters of description kept in compact mode | 1200 | No |
| JIRA_COMPACT_MAX_COMMENT_CHARS | Max characters per comment excerpt | 800 | No |
| JIRA_COMPACT_MAX_COMMENT_COUNT | Max number of latest comments included | 5 | No |
| JIRA_COMPACT_MAX_CHANGELOG_ITEMS | Max number of recent changelog items | 10 | No |

---
## Tools

| Tool | Purpose |
|------|---------|
| get-jira-ticket | Detailed ticket info (comments, changelog, labels) |
| search-jira-tickets | JQL search with limit control |
| ticket-analysis | Root cause / impact / timeline analysis |
| knowledge-search | Knowledge base & similar issue discovery |
| ticket-triage | Priority assessment + recommendations |
| (auto-compact behavior) | When `ENABLE_JIRA_COMPACT=true` Jira tools default to compact payloads |

---
## Prompts

| Prompt | Purpose |
|--------|---------|
| customer-issue | Structured customer issue report |
| troubleshooting-guide | Step-by-step diagnostic flow |
| customer-communication | Professional response drafting |
| escalation-template | Escalation framework |
| knowledge-base-article | KB article generation |
| ticket-triage | Guided triage script |

---
## Workflow Example

```typescript
// 1. Fetch ticket
const ticket = get-jira-ticket({ ticketId: "PROD-123" })

// 2. Analyze root cause
const analysis = ticket-analysis({
  ticketId: "PROD-123",
  analysisType: "root_cause",
  additionalContext: "Intermittent DB timeouts"
})

// 3. Knowledge search
const knowledge = knowledge-search({
  topic: "database timeout",
  searchScope: "similar_issues",
  timeframe: "90d"
})

// 4. Triage
const triage = ticket-triage({ ticketId: "PROD-123", includeRecommendations: true })

// Request a raw (full) ticket if compact mode is globally enabled:
const fullTicket = get-jira-ticket({ ticketId: "PROD-123", compact: false })

// Force compact even if global flag disabled:
const compactTicket = get-jira-ticket({ ticketId: "PROD-123", compact: true })
```

---
## Security

Jira:
- Read-only operations
- Credentials isolated in env vars
- Graceful error handling

File Handling:
- Root isolation (`LOCAL_STORAGE_DIR`)
- Path traversal prevention

HTTP Mode:
- Optional bearer auth
- CORS restriction support
- Health + metrics endpoints

---
## Monitoring

Health:
```bash
curl http://localhost:3001/health
```

Metrics:
```bash
curl http://localhost:3001/metrics
# uptime, memory, tool_count
```

Inspector:
```bash
npm run inspect:mcp
```

---
## Project Structure

```
oncall-support/
├── src/
│   ├── mcp-server.ts
│   ├── prompts/
│   │   └── support.ts
│   ├── templates/
│   │   ├── oncall-support-system-prompt.md
│   │   ├── customer-issue-template.md
│   │   └── troubleshooting-guide-template.md
│   └── tools/
│       ├── jira/
│       │   ├── jira-service.ts
│       │   └── index.ts
│       └── support-automation/
│           ├── support-automation-service.ts
│           └── index.ts
├── dist/
├── oncall-files/
├── k8s/
│   └── deployment.yaml
├── Dockerfile
├── docker-compose.yml
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── README.md

---
## Compact Jira Ticket Mode

Large Jira tickets can exhaust LLM context windows. The server provides a configurable compact mode that trims payload size while preserving essential diagnostic signal.

### Activation
1. Per-request: Pass `compact: true` to `get-jira-ticket` or `search-jira-tickets`.
2. Global default: Set `ENABLE_JIRA_COMPACT=true` (individual calls can override with `compact: false`).

### What Gets Trimmed
| Field | Strategy |
|-------|----------|
| Description | Truncated to `JIRA_COMPACT_MAX_DESCRIPTION_CHARS` characters |
| Comments | Latest `JIRA_COMPACT_MAX_COMMENT_COUNT` comments; each truncated to `JIRA_COMPACT_MAX_COMMENT_CHARS` chars |
| Changelog | Most recent `JIRA_COMPACT_MAX_CHANGELOG_ITEMS` entries (field, from->to) |
| Other Fields | Key metadata (id, key, summary, status, labels, assignee) retained fully |

### Environment Tuning
Adjust these env vars (examples shown with defaults):
```env
ENABLE_JIRA_COMPACT=true
JIRA_COMPACT_MAX_DESCRIPTION_CHARS=1200
JIRA_COMPACT_MAX_COMMENT_CHARS=800
JIRA_COMPACT_MAX_COMMENT_COUNT=5
JIRA_COMPACT_MAX_CHANGELOG_ITEMS=10
```

### Override Examples
```typescript
// Global compact enabled but need the full ticket:
const ticketFull = get-jira-ticket({ ticketId: "OPS-42", compact: false })

// Global compact disabled but still want a lightweight payload:
const ticketSlim = get-jira-ticket({ ticketId: "OPS-42", compact: true })
```

### Markdown Rendering
Support automation tools consume the compact representation to build concise markdown summaries (limited description excerpt, trimmed comments, recent changelog).

### Benefits
* Lower token usage per operation.
* Faster model responses.
* Consistent payload size for downstream prompts.
* Simple toggle & granular limits via env.

---
## Enhanced Triage Capability

The `ticket-triage` tool now performs advanced analysis similar to the dedicated triager project, without mutating Jira (read‑only). It produces a structured markdown report with:

### Data Extracted
| Category | Details |
|----------|---------|
| Core Fields | key, summary, issue type, priority, status, reporter, assignee, components, labels |
| Timing | Age (hours & days), hours since last update |
| Environment | Parsed firm, engagement ID, region from any URLs found in description |
| Priority Heuristics | Outage / data-loss / security / performance keyword detection |
| Duplicates | Top 0–5 potential duplicate tickets (summary similarity heuristic) |

### Heuristic Priority Escalation
If outage, data loss, or security indicators are detected and current priority < Critical, a recommendation to escalate is included.

### Recommended Labels
Automatically suggests adding labels: `outage`, `data-loss`, `security-review`, `performance`, `duplicate-review`, and always `ai-triaged` (only suggestions – not applied automatically).

### Sections Generated
1. Ticket Overview
2. Triage Metrics
3. Priority Indicators (with escalation suggestion if triggered)
4. Environment Details (only if URLs detected)
5. Potential Duplicates (if any issues match heuristic search)
6. Issue Description
7. Triage Recommendations (when `includeRecommendations=true`)
8. Next Steps Checklist

### Parameters
| Param | Type | Default | Purpose |
|-------|------|---------|---------|
| `ticketId` | string | required | Ticket key/id to triage |
| `includeRecommendations` | boolean | false | Adds action items & checklist |
| `enhanced` | boolean | true | Disable to fall back to basic triage (metrics + indicators only) |

### Example Usage
```typescript
// Basic triage (enhanced by default)
const triage = ticket-triage({ ticketId: "PROD-123" });

// With recommendations
const triageWithRec = ticket-triage({ ticketId: "PROD-123", includeRecommendations: true });

// Force basic mode (no env parsing / duplicates / heuristics)
const triageBasic = ticket-triage({ ticketId: "PROD-123", enhanced: false });
```

### What Is NOT Done Automatically
The server remains read-only: no field updates, transitions, or label mutations are performed. Actions like adding `ai-triaged`, changing priority, or setting component/area must be executed manually outside this tool.

### Future Enhancements (Optional)
| Feature | Benefit | Considerations |
|---------|---------|---------------|
| Field Update Tool | Apply recommended labels/priority directly | Requires write permissions; security review |
| Component-Area Suggestion | Map services to cascading select field | Needs metadata source integration |
| SLA Breach Time Calculation | Precise SLA risk metrics | Requires org SLA policy config |
| Transition Guidance | Suggest next workflow state | Needs project-specific transition metadata |

---
```

---
## Development & Testing

```bash
npm run dev            # STDIO dev
npm run dev:http       # HTTP dev
npm run build          # Compile
npm start              # STDIO run
npm run start:http     # HTTP run
npm test               # Unit tests (Vitest)
npm run test:coverage  # Coverage
npm run inspect:mcp    # MCP Inspector
```

### Integration Tests

Live Jira integration tests (requires valid `.env` configuration):

```bash
# Run all integration tests
node test/jira-integration.test.mjs all

# Run specific test suites
node test/jira-integration.test.mjs triage      # Triage analysis
node test/jira-integration.test.mjs comment     # Simple comment
node test/jira-integration.test.mjs workflow    # Full workflow (comment, labels, transitions)

# Configure test ticket (optional, defaults to AI-896)
$env:TEST_TICKET_ID="AI-123"; node test/jira-integration.test.mjs all
```

Test coverage:
- ✅ Triage analysis with recommendations
- ✅ Public comment posting
- ✅ Field updates (labels, priority, components)
- ✅ Workflow transitions
- ✅ Metadata queries (transitions, field options)

### Test Scripts

```bash
npm test                    # Run unit tests (Vitest)
npm run test:coverage       # Unit tests with coverage
npm run test:comprehensive  # Full test suite (type-check, build, unit tests)
npm run test:structure      # Test server structure and configuration
npm run test:jira           # Run Jira integration tests
npm run test:all            # Run comprehensive + integration tests
```

### Manual MCP Client Testing

The `test-mcp-client.ts` file allows you to manually test the MCP server:

```bash
# Compile and run (requires server to be built first)
npm run build
npx tsx test/test-mcp-client.ts
```

This will:
1. Start the MCP server
2. Connect a test client
3. List all available tools and prompts
4. Test sample tool/prompt calls
5. Report results

Docker:
```bash
docker build -t oncall-support-mcp:latest .
docker run -p 3001:3001 oncall-support-mcp:latest
curl http://localhost:3001/health
```

Kubernetes:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods -l app=oncall-support
kubectl port-forward deploy/oncall-support-mcp 3001:3001
```

---
## Extending

Add a Tool:
```typescript
export const newTool = {
  name: "new-tool",
  description: "Short description",
  schema: { param: z.string().describe("Parameter description") },
  handler: async ({ param }) => ({
    content: [{ type: "text", text: `Result: ${param}` }]
  })
};
```

Add a Prompt:
```typescript
server.prompt(
  "your-prompt",
  "Prompt description",
  { param: z.string().describe("Parameter") },
  async ({ param }) => ({
    messages: [{ role: "user", content: { type: "text", text: `Template for ${param}` } }]
  })
);
```

---
## Roadmap

| Item | Status |
|------|--------|
| Resources support | Backlog |
| Extended metrics | Backlog |
| Rate limiting | Backlog |
| OpenTelemetry tracing | Backlog |

---
## Contributing
1. Fork & branch (`feature/xyz`)
2. Implement change + tests
3. Run tests
4. Update docs
5. Open Pull Request

---
## License
MIT License – see `LICENSE`.

---
## Production Readiness

| Aspect | Status |
|--------|--------|
| Unified architecture | ✅ |
| Type safety (TS) | ✅ |
| Security controls | ✅ |
| Dual transports | ✅ |
| Health & metrics | ✅ |
| Container/K8s | ✅ |
| Documentation | ✅ |

---
## Support
- GitHub Issues (bugs/features)
- MCP Spec: https://modelcontextprotocol.io/

---
**Ready to enhance oncall support with AI?** Start in STDIO mode, expand to HTTP when needed. 🚀

- ✅ **Type Safety** - Full TypeScript with optimized strict checking- **Basic Authentication**: Uses username and API token# Run specific test suites├── TOOL_COMPARISON.md         # Feature comparison

- ✅ **Security** - Multiple layers of security controls

- ✅ **Documentation** - Complete setup and usage guides- **Read-only Operations**: Server only reads Jira data, no modifications

- ✅ **Dual Transport** - STDIO and HTTP modes

- ✅ **Error Handling** - Graceful error management throughout- **Error Handling**: Graceful handling of authentication and permission errorsnpm run test:startup└── README.md                  # This file

- ✅ **Modern Tooling** - Vitest, TypeScript 5+, ESM modules

- ✅ **OAuth Support** - Multi-provider authentication for HTTP mode

- ✅ **Docker Ready** - Development and production containers

### HTTP Mode Securitynpm run test:error-handling```

---

- **OAuth 2.0**: Multi-provider authentication

**Ready to enhance your oncall support with AI?** 🚀

- **CORS Protection**: Configurable CORS policiesnpm run test:integration

Start with STDIO mode for local Claude Desktop integration, or deploy HTTP mode for company-wide access.

- **Helmet Integration**: Security headers automatically applied

- **Rate Limiting**: Protection against abuse## ✨ Features



## 🛠️ Development# Run tests with coverage



### Project Structurenpm run test:coverage### 🛠️ Tools (Model-Controlled Actions)

```

oncall-support/- **get-jira-ticket**: Retrieve detailed ticket information with comments and history

├── src/

│   ├── mcp-server.ts           # Main MCP server implementation# Run tests with UI- **search-jira-tickets**: JQL-based search with configurable result limits

│   ├── __tests__/              # Comprehensive test suite

│   │   ├── error-handling.test.tsnpm run test:ui- **draft-ticket-questions**: Generate context-aware support questions

│   │   ├── integration.test.ts

│   │   ├── server-startup.test.ts```- **ticket-analysis**: Root cause, impact, and timeline analysis

│   │   ├── simple.test.ts

│   │   └── webhook.test.ts (skipped)- **knowledge-search**: Search knowledge base with scoped queries

│   ├── auth/                   # OAuth implementations

│   │   └── oauth.ts### Test Coverage- **ticket-triage**: Automated triage with priority assessment

│   ├── prompts/                # Structured prompt templates

│   │   └── support.ts- **execute-command**: Secure command execution with whitelist filtering

│   ├── resources/              # Advanced resource handlers

│   │   └── advanced.ts- ✅ **45 passing tests** across 4 test suites

│   ├── storage/                # Simple storage implementations

│   │   └── simple-storage.ts- ✅ Error handling scenarios

│   ├── tools/                  # Integration tools

│   │   └── integrations.ts- ✅ Server startup validation### 📁 Resources (Application-Driven Data Access)

│   └── templates/              # HTML templates for OAuth

├── dist/                       # Compiled output- ✅ Integration testing- **file://oncall-files/{path}**: Access local storage files for context

├── oncall-files/              # Local file storage

├── archive/                    # Historical docs and old implementations- ✅ Security validation- **jira://tickets/{ticket_id}**: Read-only Jira ticket data access

│   ├── old-docs/              # Archived documentation

│   └── webhook-processor/     # Future webhook integration- **system://logs/{log_type}**: System logs and configuration access

├── package.json

├── tsconfig.json              # Optimized TypeScript config## 🌐 Deployment Modes

├── vitest.config.ts           # Test configuration

└── README.md                  # This file### 📋 Prompts (User-Controlled Workflows)

```

### STDIO Mode (Local Development)- **incident-response**: Structured incident handling workflow

### Adding New Tools

- **ticket-analysis**: Root cause analysis framework (root_cause, impact, timeline)

To add a new tool to the server:

For use with Claude Desktop or local MCP clients:- **troubleshooting-guide**: Component-specific troubleshooting procedures

1. **Define the Tool**

   ```typescript- **knowledge-search**: Information discovery and search templates

   server.tool(

     "your-tool-name",```bash

     "Description of what the tool does",

     {npm start### 🔒 Security Features

       param1: z.string().describe("Parameter description"),

       param2: z.number().optional().describe("Optional parameter")```- Command execution whitelist filtering

     },

     async ({ param1, param2 }) => {- Path traversal prevention

       // Tool implementation

       return{### HTTP Mode (Network Deployment)- Optional Bearer token authentication

         content: [{

           type: "text",- Company domain restrictions

           text: "Tool output"

         }]For company-wide access via HTTP:

       };

     }

   );

   ``````bash



2. **Handle Errors**npm run start:http## 🚀 Quick Start

   ```typescript

   try {```

     // Tool logic

   } catch (error) {### Python Version (Recommended)

     return {

       content: [{Access endpoints:

         type: "text",

         text: `Error: ${error.message}`- Health check: `http://localhost:3000/health`#### Local Development (Claude Desktop)

       }],

       isError: true- OAuth demos: `http://localhost:3000/oauth-demo````bash

     };

   }- API documentation: Available via HTTP endpointscd python-version

   ```

pip install -r requirements.txt

### TypeScript Configuration

## 💡 Usage Examplescp .env.example .env

Optimized with [Total TypeScript](https://www.totaltypescript.com/tsconfig-cheat-sheet) best practices:

- Modern module system (`NodeNext`)# Edit .env with your Jira credentials

- Strict type checking enabled

- Enhanced safety with `noUncheckedIndexedAccess` and `noImplicitOverride`### Incident Response Workflowpython run_server.py --mode stdio

- Source maps for debugging

- `verbatimModuleSyntax` for better ESM/CJS interop```



### Development Commands```typescript



```bash// 1. Get ticket details#### Network Deployment (Company-wide)

# Run in development mode (STDIO)

npm run devget-jira-ticket({ ticketId: "PROD-123" })```bash



# Run in development mode (HTTP)cd python-version

npm run dev:http

// 2. Generate contextual questionspip install -r requirements.txt

# Build for production

npm run builddraft-ticket-questions({ cp .env.example .env



# Start production server  ticketId: "PROD-123",# Edit .env with your configuration

npm start

  context: "Database connection timeout errors"python run_server.py --mode network --port 8000

# Type checking

npm run type-check})```



# Linting

npm run lint

npm run lint:fix// 3. Analyze root cause#### Test the Server



# Clean build artifactsticket-analysis({```bash

npm run clean

```  ticketId: "PROD-123",# Test STDIO mode



## 🧪 Testing Guide  analysisType: "root_cause"python test_client.py



### Automated Tests})



```bash# Test network mode (in another terminal)

# Run all tests

npm test// 4. Search knowledgecurl http://localhost:8000/health



# Run specific test suitesknowledge-search({

npm run test:error-handling

npm run test:startup  topic: "database timeout",

npm run test:integration

  searchScope: "similar_issues"```

# Run with UI

npm run test:ui})



# Run with coverage (requires @vitest/coverage-v8)### TypeScript Version

npm run test:coverage

```// 5. Execute fix commands



**Test Coverage:**execute-command({```bash

- ✅ 45 passing tests across 4 test suites

- ✅ Error handling scenarios  command: "npm run restart-database",cd ts-version

- ✅ Server startup validation

- ✅ Integration testing  workingDirectory: "./project"npm install

- ✅ Security validation

})npm run build

### Manual MCP Client Tests (Claude Desktop)

```npm start

#### Test 1: Basic Server Connection

**Prompt:** `What MCP tools are available? Can you show me the oncall support tools?````



**Expected:** You should see 8 oncall support tools listed## 🚧 Potential Future Enhancements



#### Test 2: Jira Integration## 🎯 Implementation Comparison

```

# Get ticket details### Webhook Integration (Planned)

"Use the get-jira-ticket tool to retrieve details for ticket 'PROJ-123'"

| Feature | TypeScript | Python |

# Search tickets

"Use the search-jira-tickets tool with JQL 'project = PROJ AND status = Open'"A webhook processor implementation is available in `archive/webhook-processor/` for future integration. This would enable:|---------|------------|--------|



# Generate questions| **MCP Components** | Tools only | **Tools + Resources + Prompts** |

"Use the draft-ticket-questions tool for ticket 'PROJ-123' with context 'Production outage'"

```- **Real-time Jira Event Processing** - Automatic handling of ticket updates| **Architecture** | Basic MCP | **Complete MCP specification** |



#### Test 3: Support Automation- **Event-Driven Workflows** - Trigger actions based on Jira webhooks| **Tools** | 5 tools | 5 tools |

```

# Analyze ticket- **Queue-Based Processing** - Asynchronous event handling with AWS Bedrock| **Resources** | ❌ None | ✅ **3 resource templates** |

"Use the ticket-analysis tool to perform root cause analysis for ticket 'PROD-123'"

- **Multi-Channel Notifications** - Integration with Slack, Teams, or email| **Prompts** | ❌ None | ✅ **4 workflow templates** |

# Search knowledge base

"Use the knowledge-search tool to find similar issues about 'database timeout'"| **Claude Desktop** | ✅ STDIO | ✅ STDIO |



# Triage ticketThe webhook implementation includes:| **Network Deployment** | ❌ No | ✅ **Full HTTP REST API** |

"Use the ticket-triage tool to assess priority for ticket 'PROD-123'"

```- Jira webhook validation and signature verification| **Multi-user Support** | ❌ No | ✅ **Concurrent access** |



#### Test 4: Command Execution- AWS Bedrock integration for AI-powered analysis| **Authentication** | ❌ No | ✅ **Token-based security** |

```

# Safe commands- Event queue management| **API Documentation** | ❌ No | ✅ **FastAPI auto-docs** |

"Use the execute-command tool to run 'npm --version'"

"Use the execute-command tool to run 'git status'"- MCP client integration for tool execution| **Health Monitoring** | ❌ No | ✅ **Built-in endpoints** |



# Security test (should be blocked)| **Container Ready** | ✅ Basic | ✅ **Production-ready** |

"Use the execute-command tool to run 'rm -rf /'"

```To explore webhook functionality, see `archive/webhook-processor/README.md`.



#### Test 5: Complete Workflow## 🔧 Configuration

```

"Let's test a complete oncall workflow:### Other Potential Features

1. Use search-jira-tickets to find tickets with 'critical' in summary

2. Use get-jira-ticket to get details for the first one### Environment Variables

3. Use draft-ticket-questions to generate questions

4. Use ticket-analysis to perform root cause analysis- **Resource Templates** - Structured data access patterns

5. Use execute-command to run 'git status'"

```- **Advanced Prompts** - More workflow templates```env



### ✅ Success Indicators- **Multi-Provider OAuth** - Extended authentication options# Jira Integration

- Tools appear in Claude's response

- Commands execute successfully- **Rate Limiting** - API usage controlsJIRA_BASE_URL=https://your-company.atlassian.net

- Jira integration works (if credentials configured)- **Caching Layer** - Redis integration for performanceJIRA_USERNAME=your-email@company.com

- Error messages are clear and helpful

- **Monitoring** - OpenTelemetry tracing and metricsJIRA_API_TOKEN=your-jira-api-token

### ❌ Failure Indicators

- "Tool not found" errors

- "Server disconnected" messages

- Commands fail to execute## 🛡️ Security Best Practices# Security

- Files don't download or can't be read

ALLOWED_COMMANDS=^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$

## 🐛 Troubleshooting

### Command ExecutionMAX_DOWNLOAD_SIZE=104857600

### Common Issues

AUTH_TOKEN=optional-bearer-token

**Jira Authentication Errors**

- Verify `JIRA_BASE_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN` are correct- Only whitelisted command patterns are allowedCOMPANY_DOMAIN=optional-domain-restriction

- Check that the API token has appropriate permissions

- Ensure the Jira instance is accessible from your network- Commands execute in controlled environments



**Command Execution Blocked**- All command executions are logged# Storage

- Check the `ALLOWED_COMMANDS` regex pattern

- Add your command pattern to the allowed listLOCAL_STORAGE_DIR=./oncall-files

- Use absolute paths for commands if needed



**Server Won't Start**# Network Server (Python only)

- Check that Node.js 18+ is installed

- Verify all dependencies are installed (`npm install`)HOST=0.0.0.0

- Check for port conflicts (HTTP mode uses port 3000 by default)

- Review environment variables in `.env`PORT=8000



### Debug ModeDEBUG=false

Enable debug logging by setting:

```bashCORS_ENABLED=true

DEBUG=mcp:*

npm run devALLOWED_ORIGINS=*

```

```

## 🐳 Docker Support

### API Security### 💻 Claude Desktop Setup & Configuration



### DevelopmentSee version-specific README sections. Python recommended for full MCP coverage.

```bash

docker-compose up -d- Jira credentials stored in environment variables only

```

- Read-only Jira operations (no modifications)

### Production Build

```bash- Optional OAuth for HTTP mode

docker build -t oncall-support-mcp .

docker run -p 3000:3000 --env-file .env oncall-support-mcp- CORS and Helmet security headers

```

Add to your `claude_desktop_config.json`:

## 🐳 Docker Support

## 🔧 Development

### Development

```bash**macOS/Linux:**

docker-compose up -d

```### TypeScript Configuration```json



### Production Build{

```bash

docker build -t oncall-support-mcp .Optimized with Total TypeScript best practices:  "mcpServers": {

docker run -p 3000:3000 --env-file .env oncall-support-mcp

```- Modern module system (`NodeNext`)    "oncall-support": {



## 🚧 Future Enhancements- Strict type checking enabled      "command": "python",



### Webhook Integration (Planned)- Enhanced safety with `noUncheckedIndexedAccess`      "args": ["-m", "oncall_support.server"],



A webhook processor implementation is available in `archive/webhook-processor/` for future integration. This would enable:- Source maps for debugging      "cwd": "path/to/oncall-support/python-version"



- **Real-time Jira Event Processing** - Automatic handling of ticket updates    }

- **Event-Driven Workflows** - Trigger actions based on Jira webhooks

- **Queue-Based Processing** - Asynchronous event handling with AWS Bedrock### Adding New Tools  }

- **Multi-Channel Notifications** - Integration with Slack, Teams, or email

}

The webhook implementation includes:

- Jira webhook validation and signature verification```typescript```

- AWS Bedrock integration for AI-powered analysis

- Event queue managementserver.tool(

- MCP client integration for tool execution

  "tool-name",**Windows:**

To explore webhook functionality, see `archive/webhook-processor/README.md`.

  "Tool description for AI context",```json

### Other Potential Features

  {{

- **Advanced Resources** - Structured data access patterns

- **Extended Prompts** - More workflow templates    param: z.string().describe("Parameter description")  "mcpServers": {

- **Rate Limiting** - API usage controls

- **Caching Layer** - Redis integration for performance  },    "oncall-support": {

- **Monitoring** - OpenTelemetry tracing and metrics

- **Multi-Workspace Support** - Handle multiple Jira instances  async ({ param }) => {      "command": "python",



## 🤝 Contributing    // Implementation      "args": ["-m", "oncall_support.server"],



1. Fork the repository    return {      "cwd": "path\\to\\oncall-support\\python-version"

2. Create a feature branch (`git checkout -b feature/amazing-feature`)

3. Make your changes      content: [{ type: "text", text: "Result" }]    }

4. Add tests for new functionality

5. Ensure all tests pass (`npm test`)    };  }

6. Update documentation as needed

7. Commit your changes (`git commit -m 'Add amazing feature'`)  }}

8. Push to the branch (`git push origin feature/amazing-feature`)

9. Open a Pull Request);```



## 📄 License```



This project is licensed under the MIT License - see the LICENSE file for details.## 🌐 Network API Reference



## 🆘 Support### Code Quality



For issues and questions:The Python version provides a complete REST API for all MCP components:

1. Check the troubleshooting section above

2. Review the [MCP documentation](https://modelcontextprotocol.io/)```bash

3. Check `archive/old-docs/` for detailed technical documentation

4. Open an issue in the [GitHub repository](https://github.com/leonxuecloud/My-playgroud)# Type checking### Tools Endpoints

5. Contact your system administrator for Jira access issues

npm run type-check```

## 🏆 Production Ready Checklist

POST /mcp/tools/get-jira-ticket

This implementation is production-ready with:

# LintingPOST /mcp/tools/search-jira-tickets

- ✅ **Comprehensive Testing** - 45+ tests covering all major functionality

- ✅ **Type Safety** - Full TypeScript with optimized strict checkingnpm run lintPOST /mcp/tools/draft-ticket-questions

- ✅ **Security** - Multiple layers of security controls

- ✅ **Documentation** - Complete setup and usage guidesnpm run lint:fixPOST /mcp/tools/ticket-analysis

- ✅ **Dual Transport** - STDIO and HTTP modes

- ✅ **Error Handling** - Graceful error management throughoutPOST /mcp/tools/knowledge-search

- ✅ **Modern Tooling** - Vitest, TypeScript 5+, ESM modules

- ✅ **OAuth Support** - Multi-provider authentication for HTTP mode# BuildPOST /mcp/tools/ticket-triage

- ✅ **Docker Ready** - Development and production containers

npm run buildPOST /mcp/tools/execute-command

---

# Clean build

**Ready to enhance your oncall support with AI?** 🚀

npm run clean

Start with STDIO mode for local Claude Desktop integration, or deploy HTTP mode for company-wide access.

```### Resources Endpoints

```

## 📚 DocumentationGET /mcp/resources/oncall-files/{path}

GET /mcp/resources/jira/tickets/{ticket_id}

- **Current Documentation**: This READMEGET /mcp/resources/system/logs/{log_type}

- **Historical Documentation**: See `archive/old-docs/` for:GET /mcp/resources (list all templates)

  - Architecture documentation```

  - Design documents

  - Deployment guides### Prompts Endpoints

  - Usage examples```

  - Tool comparisonsPOST /mcp/prompts/incident-response

POST /mcp/prompts/ticket-analysis

## 🐳 Docker SupportPOST /mcp/prompts/troubleshooting-guide

POST /mcp/prompts/knowledge-search

```bashGET  /mcp/prompts (list all templates)

# Development```

docker-compose up -d

### System Endpoints

# Production build```

docker build -t oncall-support-mcp .GET /           (server information)

GET /health     (health check)

# Run containerGET /docs       (API documentation)

docker run -p 3000:3000 --env-file .env oncall-support-mcp```

```

## 📖 Usage Examples

## 🤝 Contributing

### Using Tools

1. Fork the repository```python

2. Create a feature branch (`git checkout -b feature/amazing-feature`)# Get a Jira ticket

3. Make your changesresult = await get_jira_ticket("PROJ-123")

4. Add tests for new functionality

5. Ensure all tests pass (`npm test`)# Search for tickets

6. Update documentation as neededtickets = await search_jira_tickets("project = PROJ AND status = Open")

7. Commit your changes (`git commit -m 'Add amazing feature'`)

8. Push to the branch (`git push origin feature/amazing-feature`)# Download a file

9. Open a Pull Requestawait download_file("https://example.com/report.pdf", "incident-report.pdf")

```

## 📄 License

### Using Resources

This project is licensed under the MIT License.```python

# Access local files for context

## 🆘 Supportfile_content = await read_oncall_file("logs/error.log")



- **Issues**: Open a GitHub issue for bugs or feature requests# Get Jira ticket data as a resource

- **Documentation**: Check `archive/old-docs/` for detailed technical documentationticket_data = await read_jira_ticket_resource("PROJ-123")

- **Questions**: Review closed issues or open a new discussion```



## 🏆 Production Ready### Using Prompts

```python

This implementation is production-ready with:# Generate incident response workflow

workflow = await incident_response(

- ✅ **Comprehensive Testing** - 45+ tests covering all major functionality    incident_type="outage",

- ✅ **Type Safety** - Full TypeScript with strict checking    severity="high", 

- ✅ **Security** - Multiple layers of security controls    affected_systems="api-gateway",

- ✅ **Documentation** - Complete setup and usage guides    initial_symptoms="5xx errors increasing"

- ✅ **Dual Transport** - STDIO and HTTP modes)

- ✅ **Error Handling** - Graceful error management throughout

- ✅ **Modern Tooling** - Vitest, TypeScript 5+, ESM modules# Create ticket analysis framework

---```

**Ready to enhance your oncall support with AI?** 🚀## 🐳 Docker Deployment



Start with STDIO mode for local Claude Desktop integration, or deploy HTTP mode for company-wide access.### Python Version

```bash
cd python-version


### Custom Docker Build
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "run_server.py", "--mode", "network"]
```

## 🧪 Testing

### Python Version
```bash
cd python-version
python -m pytest tests/
python final_test.py
```

### TypeScript Version
cd ts-version
npm test
npm run test:integration
```

## 📚 Documentation

- **[Design Document](DESIGN_DOCUMENT.md)**: Complete architecture and technical specifications
- **[Tool Comparison](TOOL_COMPARISON.md)**: Detailed feature comparison between implementations
- **[MCP Specification](https://modelcontextprotocol.io/docs/learn/server-concepts)**: Official MCP documentation
- **[Python README](python-version/README.md)**: Python-specific documentation
- **[TypeScript README](ts-version/README.md)**: TypeScript-specific documentation

## 🔧 Development

### Adding New Tools
```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Tool description."""
    # Implementation
```

### Adding New Resources
```python
async def my_resource(id: str) -> str:
    """Resource description."""
    # Implementation
    return "data"
```

### Adding New Prompts
```python
@mcp.prompt()
async def my_prompt(param: str) -> str:
    """Prompt description."""
    # Generate structured template
```

## 🤝 Contributing

1. Fork the repository
3. Make your changes
4. Add tests
5. Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support
- **Issues**: GitHub Issues (project-specific)
- **Documentation**: See docs & design files


### ✅ Complete MCP Specification
- **All 3 Components**: Tools, Resources, and Prompts
- **Best Practices**: Follows official MCP patterns
- **Future-Proof**: Ready for MCP ecosystem evolution

### ✅ Production Ready
- **Monitoring**: Health checks, logging, metrics
- **Well Tested**: Comprehensive test suites

---

**Ready to enhance your oncall support with AI?** 🚀

Roadmap will introduce network deployment & extended MCP components; current scope focuses on reliable tool execution via STDIO.
**🛠️ TOOLS (5)** - Model-controlled active operations:
- **Local Files**: `file://oncall-files/{path}`
- **System Logs**: `system://logs/{log_type}`

**📋 PROMPTS (4)** - User-controlled structured templates:
- **Incident Response**: Step-by-step incident handling
- **Ticket Analysis**: Root cause analysis framework
- **Troubleshooting**: Component-specific guides

### Deployment Modes

```
┌─────────────────────────────────────────────────────┐
│  STDIO Mode              │    Network Mode          │
│  (Claude Desktop)        │    (Company Network)     │
│                          │                          │
│  Claude ↔ MCP Server     │  HTTP Clients ↔ REST API │
│  • Local development     │  • Multi-user access     │
│  • Direct AI integration │  • Web applications      │
│  • Real-time interaction │  • Microservice arch     │
└─────────────────────────────────────────────────────┘
```

## 🎯 **Project Summary**

### **✅ Complete Implementation**
- **5 Production-Ready Tools**: Jira integration and support automation
- **29 Comprehensive Tests**: Error handling, startup validation, security checks
- **TypeScript Implementation**: Full type safety and modern development practices
- **Security Features**: Command whitelist, path validation
- **Docker Support**: Development and production environments
- **Complete Documentation**: Setup guides, usage examples, troubleshooting

```bash
# 1. Navigate to project
cd mcp-server-examples/oncall-support

# 2. Install dependencies
npm install

# 3. Configure environment
# Edit .env with your Jira credentials

# 4. Build and start
npm run build
npm start
```

### **🧪 Testing**
# Run all tests
npm test

# Run specific test suites
npm run test:error-handling
npm run test:startup

npm run test:coverage
```

**macOS/Linux:**
```json
{
  "mcpServers": {
    "oncall-support": {
      "command": "node",
      "args": ["dist/index.js"],
    }
  }
```
```json
  "mcpServers": {
    "oncall-support": {
      "command": "node",
      "cwd": "path\\to\\oncall-support"
    }
  }
```

## Features

### 🔗 Jira Integration
- **Get Jira Ticket Details**: Retrieve comprehensive information about any Jira ticket
- **Search Jira Tickets**: Use JQL (Jira Query Language) to find relevant tickets
- **Draft Ticket Questions**: Automatically generate relevant questions based on ticket content

### 🤖 AI Support Automation
- **Ticket Analysis**: Root cause, impact, and timeline analysis
- **Automated Triage**: Priority assessment with recommendations
- **Secure Command Execution**: Run system commands with configurable security restrictions
- **Pattern-based Security**: Allow only whitelisted command patterns

### 🎯 AI-Powered Insights
- **Context-Aware Question Generation**: Generate relevant questions based on ticket priority, components, and status
- **Component-Specific Questions**: Tailor questions based on affected system components
- **Priority-Based Escalation**: Generate appropriate questions for critical/high priority issues

## Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Jira API access (username and API token)

### Setup

1. **Clone and Install Dependencies**
   ```bash
   cd mcp-server-examples/oncall-support
   npm install
   ```

2. **Configure Environment Variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Jira Configuration
   JIRA_BASE_URL=https://your-company.atlassian.net
   JIRA_USERNAME=your-email@company.com
   JIRA_API_TOKEN=your-jira-api-token
   
   # Security Configuration
   ALLOWED_COMMANDS=^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$
   MAX_DOWNLOAD_SIZE=104857600
   LOCAL_STORAGE_DIR=./oncall-files
   ```

3. **Build the Server**
   ```bash
   npm run build
   ```

4. **Start the Server**
   ```bash
   npm start
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JIRA_BASE_URL` | Your Jira instance URL | - | Yes |
| `JIRA_USERNAME` | Your Jira username/email | - | Yes |
| `JIRA_API_TOKEN` | Your Jira API token | - | Yes |
| `ALLOWED_COMMANDS` | Regex pattern for allowed commands | `^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$` | No |
| `MAX_DOWNLOAD_SIZE` | Maximum file download size in bytes | `104857600` (100MB) | No |
| `LOCAL_STORAGE_DIR` | Directory for downloaded files | `./oncall-files` | No |

### Jira API Token Setup

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive name (e.g., "MCP Server")
4. Copy the token and use it as `JIRA_API_TOKEN`

## Usage

### Available Tools

#### 1. Jira Operations

**Get Jira Ticket Details**
```typescript
get-jira-ticket({
  ticketId: "PROJ-123"
})
```

**Search Jira Tickets**
```typescript
search-jira-tickets({
  jql: "project = PROJ AND status = 'In Progress'",
  maxResults: 5
})
```

**Draft Ticket Questions**
```typescript
draft-ticket-questions({
  ticketId: "PROJ-123",
  context: "Production outage affecting payment system"
})
```

#### 2. Support Automation

**Ticket Analysis**
```typescript
ticket-analysis({
  ticketId: "PROD-123",
  analysisType: "root_cause",
  additionalContext: "Database timeout errors"
})
```

**Knowledge Search**
```typescript
knowledge-search({
  topic: "database timeout",
  searchScope: "similar_issues",
  timeframe: "90d"
})
```

**Ticket Triage**
```typescript
ticket-triage({
  ticketId: "PROD-123",
  includeRecommendations: true
})
```

#### 3. Command Execution

**Execute Command**
```typescript
execute-command({
  command: "npm install",
  workingDirectory: "./project"
})
```

### Example Workflows

#### Incident Response Workflow

1. **Get Ticket Details**
   ```typescript
   get-jira-ticket({ ticketId: "PROD-123" })
   ```

2. **Generate Questions**
   ```typescript
   draft-ticket-questions({ 
     ticketId: "PROD-123",
     context: "Database connection timeout errors"
   })
   ```

3. **Analyze Root Cause**
   ```typescript
   ticket-analysis({
     ticketId: "PROD-123",
     analysisType: "root_cause"
   })
   ```

4. **Search Knowledge Base**
   ```typescript
   knowledge-search({
     topic: "database connection timeout",
     searchScope: "similar_issues"
   })
   ```

5. **Execute Fix Commands**
   ```typescript
   execute-command({
     command: "npm run restart-database",
     workingDirectory: "./project"
   })
   ```

## Security Features

### Command Execution Security
- **Pattern-based Whitelisting**: Only allows commands matching the `ALLOWED_COMMANDS` regex
- **Default Safe Commands**: npm, yarn, git, ls, cat, grep, find, mkdir, rmdir, cp, mv, chmod, chown
- **Working Directory Control**: Commands execute in specified directories

### Jira API Security
- **Basic Authentication**: Uses username and API token
- **Read-only Operations**: Server only reads Jira data, no modifications
- **Error Handling**: Graceful handling of authentication and permission errors

## Development

### Project Structure
```
oncall-support/
├── src/
│   └── index.ts          # Main server implementation
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── env.example           # Environment variables template
└── README.md            # This file
```

### Adding New Tools

To add a new tool to the server:

1. **Define the Tool**
   ```typescript
   server.tool(
     "your-tool-name",
     "Description of what the tool does",
     {
       param1: z.string().describe("Parameter description"),
       param2: z.number().optional().describe("Optional parameter")
     },
     async ({ param1, param2 }) => {
       // Tool implementation
       return {
         content: [{
           type: "text",
           text: "Tool output"
         }]
       };
     }
   );
   ```

2. **Handle Errors**
   ```typescript
   try {
     // Tool logic
   } catch (error) {
     return {
       content: [{
         type: "text",
         text: `Error: ${error.message}`
       }],
       isError: true
     };
   }
   ```

### Testing

```bash
# Run in development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📚 Version-Specific Documentation
We intentionally maintain two independent README documents so each implementation can evolve at its own pace while sharing a unified high‑level overview here.

| Implementation | Location | README | Purpose |
|----------------|----------|--------|---------|
| TypeScript | `ts-version/` | `ts-version/README.md` | Original implementation focused on STDIO MCP tooling with strong type safety |
| Python | `python-version/` | `python-version/README.md` | Enhanced implementation adding Network (HTTP) mode, Resources, Prompts, and deployment features |

Use the root README (this file) for choosing a path; dive into the per‑version README for day‑to‑day development details, commands, and extended examples.

## 🧩 MCP Components Coverage
| Component | TypeScript | Python | Notes |
|-----------|-----------|--------|-------|
| Tools | ✅ (8) | ✅ (8) | Functional parity preserved |
| Resources | ⏳ (Not implemented) | ✅ (3 templates) | File, Jira ticket, system logs |
| Prompts | ⏳ (Not implemented) | ✅ (4 templates) | Incident, analysis, troubleshooting, knowledge search |
| Network HTTP API | ⏳ | ✅ | FastAPI with auth / CORS |
| STDIO (Claude Desktop) | ✅ | ✅ | Both supported |

## 🗺️ When To Use Which Version
| Scenario | Recommended Version | Rationale |
|----------|---------------------|-----------|
| Need only classic MCP tools for local use | TypeScript | Stable, familiar Node toolchain |
| Need network accessible MCP server | Python | Built-in HTTP layer & auth |
| Need Resources / Prompts per MCP spec | Python | Full 3-component coverage |
| Want to prototype new tools quickly | Python | Less boilerplate with FastMCP |
| Need strict typing & existing TS infra | TypeScript | Leverages corporate Node ecosystem |

## 🔄 Keeping Both Versions Aligned
When adding a new tool:
1. Implement in `python-version/oncall_support/server.py`
2. Mirror logic in `ts-version/src/index.ts`
3. Update `TOOL_COMPARISON.md`
4. Add tests for both (Vitest / Pytest)

For Resources & Prompts (Python only currently):
- Extend resource decorators or prompt functions in `server.py`
- Expose matching HTTP endpoints in `network_server.py`

## 🧪 Testing Matrix
| Layer | TypeScript | Python |
|-------|------------|--------|
| Tool behavior | Vitest suite | Pytest / ad-hoc scripts |
| MCP STDIO start | Startup test | Startup test |
| Network API | N/A | FastAPI route tests (future) |
| Security (command filter) | Included | Included |

## 🛤️ Roadmap Suggestions
| Item | TS | Py | Priority |
|------|----|----|----------|
| Add Resources support | ❌ | ✅ | Medium (TS parity) |
| Add Prompts support | ❌ | ✅ | Medium (TS parity) |
| Unified test harness | ❌ | ❌ | Medium |
| Add OpenTelemetry tracing | ❌ | ❌ | Low |
| Add rate limiting | ❌ | ❌ | Medium |
| Add caching (Redis) | ❌ | ❌ | Low |

## 🔐 Security Summary
- Command whitelist (regex based)
- Size limits on downloads
- Path traversal prevention
- Optional bearer token (Python network mode)
- Separation of STDIO and HTTP execution paths

## 📝 Change Management
All architectural updates should be reflected in:
- `DESIGN_DOCUMENT.md`
- `TOOL_COMPARISON.md`
- Version-specific README if behavior changes

## 📬 Questions / Next Steps
Need help extending Resources to TypeScript or adding more Prompts? Open an issue or request a feature task. Ready to proceed with further iteration—just say what you’d like next.

