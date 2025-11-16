/**
 * Unified MCP Server - Supports Both Transports
 * 
 * Same MCP core, different transport layers:
 * - stdio: For local Claude Desktop (same machine)
 * - http: For remote MCP clients via StreamableHTTP (network)
 * 
 * Usage:
 *   node dist/mcp-server.js --transport=stdio    # Local mode
 *   node dist/mcp-server.js --transport=http     # Remote mode (HTTP)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express, { type Request, type Response } from 'express';
import cors from 'cors';
import * as dotenv from "dotenv";
import { z } from "zod";
import axios from "axios";
import * as fs from "fs/promises";
import * as path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import AdmZip from "adm-zip";
import fetch from "node-fetch";
import {
  customerIssuePrompt,
  troubleshootingGuidePrompt,
  customerCommunicationPrompt,
  escalationPrompt,
  knowledgeBasePrompt,
  ticketTriagePrompt
} from "./prompts/support.js";
import { jiraService } from "./tools/jira/jira-service.js";
import { getMcpOverview } from "./tools/mcp/mcp-service.js";
import { 
  connectToRemoteMcpServer, 
  getRemoteTools, 
  getRemotePrompts,
  callRemoteTool,
  getRemotePrompt,
  getConnectionStatus
} from "./tools/mcp/mcp-client-connector.js";
import { supportAutomationService } from "./tools/support-automation/support-automation-service.js";

dotenv.config();

const execAsync = promisify(exec);

// Configuration
const ALLOWED_COMMANDS = process.env.ALLOWED_COMMANDS || "^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$";
const MAX_DOWNLOAD_SIZE = parseInt(process.env.MAX_DOWNLOAD_SIZE || "104857600");
const LOCAL_STORAGE_DIR = process.env.LOCAL_STORAGE_DIR || "./oncall-files";
// HTTP port (mutable to allow CLI override via --port=NNNN)
let HTTP_PORT = parseInt(process.env.MCP_PORT || "3001");

// Ensure storage directory exists
async function ensureStorageDir() {
  try {
    await fs.mkdir(LOCAL_STORAGE_DIR, { recursive: true });
  } catch (error) {
    console.error("Error creating storage directory:", error);
  }
}

/**
 * Create and configure the MCP server with all tools and prompts
 * This is the SAME for both stdio and HTTP transports
 */
async function createMcpServer(): Promise<McpServer> {
  const server = new McpServer({
    name: "Oncall Support Server",
    version: "1.0.0"
  });

  // Connect to remote MCP server if enabled
  if (process.env.ENABLE_MCP_SERVER === 'true') {
    // Only log if not in STDIO mode (STDIO uses stderr for JSON-RPC)
    const isStdio = process.argv.includes('--transport=stdio') || !process.argv.includes('--transport');
    if (!isStdio) {
      console.error('[MCP] Connecting to remote MCP server...');
    }
    await connectToRemoteMcpServer();
    const status = getConnectionStatus();
    if (!isStdio) {
      if (status.connected) {
        console.error(`[MCP] ✅ Connected! Found ${status.toolCount} tools and ${status.promptCount} prompts`);
      } else {
        console.error(`[MCP] ⚠️  Connection failed: ${status.error}`);
      }
    }
  }

  /* ========================================
   * JIRA SERVICE (Unified JIRA operations)
   * ======================================== */

  // Tool: Get Jira ticket details
  server.tool(
    jiraService.getTicket.name,
    jiraService.getTicket.description,
    jiraService.getTicket.schema,
    async (args: any) => {
      const result = await jiraService.getTicket.handler(args);
      return result;
    }
  );

  // Tool: Search Jira tickets
  server.tool(
    jiraService.searchTickets.name,
    jiraService.searchTickets.description,
    jiraService.searchTickets.schema,
    async (args: any) => {
      const result = await jiraService.searchTickets.handler(args);
      return result;
    }
  );

  // Tool: Add Jira comment
  server.tool(
    jiraService.addComment.name,
    jiraService.addComment.description,
    jiraService.addComment.schema,
    async (args: any) => {
      const result = await jiraService.addComment.handler(args);
      return result;
    }
  );

  // Tool: Update Jira fields
  server.tool(
    jiraService.updateFields.name,
    jiraService.updateFields.description,
    jiraService.updateFields.schema,
    async (args: any) => {
      const result = await jiraService.updateFields.handler(args);
      return result;
    }
  );

  // Tool: Transition Jira ticket
  server.tool(
    jiraService.transitionTicket.name,
    jiraService.transitionTicket.description,
    jiraService.transitionTicket.schema,
    async (args: any) => {
      const result = await jiraService.transitionTicket.handler(args);
      return result;
    }
  );

  // Tool: Get Jira transitions
  server.tool(
    jiraService.getTransitions.name,
    jiraService.getTransitions.description,
    jiraService.getTransitions.schema,
    async (args: any) => {
      const result = await jiraService.getTransitions.handler(args);
      return result;
    }
  );

  // Tool: Get Jira field options
  server.tool(
    jiraService.getFieldOptions.name,
    jiraService.getFieldOptions.description,
    jiraService.getFieldOptions.schema,
    async (args: any) => {
      const result = await jiraService.getFieldOptions.handler(args);
      return result;
    }
  );

  /* ========================================
   * SUPPORT AUTOMATION SERVICE (Unified support automation operations)
   * ======================================== */

  // Tool: Ticket Analysis - Root cause, impact, and timeline analysis
  server.tool(
    supportAutomationService.ticketAnalysis.name,
    supportAutomationService.ticketAnalysis.description,
    supportAutomationService.ticketAnalysis.schema,
    async (args: any) => {
      const result = await supportAutomationService.ticketAnalysis.handler(args);
      return result;
    }
  );

  // Tool: Knowledge Search - Search KB and documentation
  server.tool(
    supportAutomationService.knowledgeSearch.name,
    supportAutomationService.knowledgeSearch.description,
    supportAutomationService.knowledgeSearch.schema,
    async (args: any) => {
      const result = await supportAutomationService.knowledgeSearch.handler(args);
      return result;
    }
  );

  // Tool: Ticket Triage - Automated triage with recommendations
  server.tool(
    supportAutomationService.ticketTriage.name,
    supportAutomationService.ticketTriage.description,
    supportAutomationService.ticketTriage.schema,
    async (args: any) => {
      const result = await supportAutomationService.ticketTriage.handler(args);
      return result;
    }
  );

  /* ========================================
   * SUPPORT PROMPTS
   * ======================================== */

  // Register Support Prompts
  server.prompt(
    "customer-issue",
    "Generate a structured customer issue report template",
    {
      ticketId: z.string().describe("Ticket ID"),
      customerName: z.string().describe("Customer name"),
      issueType: z.string().describe("Issue type"),
      priority: z.string().optional().describe("Priority level")
    },
    async ({ ticketId, customerName, issueType, priority }) => {
      const promptText = customerIssuePrompt({ ticketId, customerName, issueType, priority });
      return {
        messages: [{
          role: "user",
          content: { type: "text", text: promptText }
        }]
      };
    }
  );

  server.prompt(
    "troubleshooting-guide",
    "Generate a troubleshooting guide",
    {
      issueName: z.string().describe("Issue name"),
      product: z.string().describe("Product name"),
      difficulty: z.string().optional().describe("Difficulty level")
    },
    async ({ issueName, product, difficulty }) => {
      const promptText = troubleshootingGuidePrompt({ issueName, product, difficulty });
      return {
        messages: [{
          role: "user",
          content: { type: "text", text: promptText }
        }]
      };
    }
  );

  server.prompt(
    "customer-communication",
    "Generate customer communication templates",
    {
      type: z.enum(['initial_response', 'update', 'resolution', 'escalation', 'apology']).describe("Communication type"),
      ticketId: z.string().describe("Ticket ID"),
      customerName: z.string().describe("Customer name"),
      issueType: z.string().optional().describe("Issue type")
    },
    async ({ type, ticketId, customerName, issueType }) => {
      const promptText = customerCommunicationPrompt({ type, ticketId, customerName, issueType });
      return {
        messages: [{
          role: "user",
          content: { type: "text", text: promptText }
        }]
      };
    }
  );

  server.prompt(
    "escalation-template",
    "Generate an escalation template",
    {
      ticketId: z.string().describe("Ticket ID"),
      customerName: z.string().describe("Customer name"),
      severity: z.enum(['critical', 'high', 'medium', 'low']).describe("Severity"),
      issueType: z.string().describe("Issue type")
    },
    async ({ ticketId, customerName, severity, issueType }) => {
      const promptText = escalationPrompt({ ticketId, customerName, severity, issueType });
      return {
        messages: [{
          role: "user",
          content: { type: "text", text: promptText }
        }]
      };
    }
  );

  server.prompt(
    "knowledge-base-article",
    "Generate a knowledge base article template",
    {
      articleTitle: z.string().describe("Article title"),
      category: z.string().describe("Article category")
    },
    async ({ articleTitle, category }) => {
      const promptText = knowledgeBasePrompt({ articleTitle, category });
      return {
        messages: [{
          role: "user",
          content: { type: "text", text: promptText }
        }]
      };
    }
  );

  /* ========================================
   * MCP REMOTE METADATA (Optional)
   * ======================================== */
  if (process.env.ENABLE_MCP_SERVER === 'true') {
    server.tool(
      'list-mcp-metadata',
      'List remote MCP server tools & prompts (cached if previously fetched)',
      {
        forceRefresh: z.boolean().optional().describe('Force refetch from remote instead of cache')
      },
      async ({ forceRefresh }: { forceRefresh?: boolean }) => {
        const overview = await getMcpOverview(!!forceRefresh);
        return {
          content: [{ type: 'text' as const, text: overview }]
        };
      }
    );

    // Dynamically register remote tools as proxy tools
    const remoteTools = getRemoteTools();
    const isStdio = process.argv.includes('--transport=stdio') || !process.argv.includes('--transport');
    for (const tool of remoteTools) {
      const toolName = `remote-${tool.name}`;
      if (!isStdio) {
        console.error(`[MCP] Registering remote tool: ${toolName}`);
      }
      
      server.tool(
        toolName,
        tool.description || `Remote tool: ${tool.name}`,
        tool.inputSchema,
        async (args: any) => {
          try {
            const result = await callRemoteTool(tool.name, args);
            return result;
          } catch (error: any) {
            return {
              content: [{
                type: 'text' as const,
                text: `Error calling remote tool: ${error.message}`
              }],
              isError: true
            };
          }
        }
      );
    }

    // Dynamically register remote prompts
    const remotePrompts = getRemotePrompts();
    for (const prompt of remotePrompts) {
      const promptName = `remote-${prompt.name}`;
      if (!isStdio) {
        console.error(`[MCP] Registering remote prompt: ${promptName}`);
      }
      
      // Build arguments schema from prompt.arguments
      const argsObj: Record<string, any> = {};
      if (prompt.arguments) {
        for (const arg of prompt.arguments) {
          argsObj[arg.name] = z.string().optional().describe(arg.description || arg.name);
        }
      }
      
      server.prompt(
        promptName,
        prompt.description || `Remote prompt: ${prompt.name}`,
        argsObj,
        async (args: any) => {
          try {
            const result = await getRemotePrompt(prompt.name, args);
            return result;
          } catch (error: any) {
            return {
              messages: [{
                role: "user",
                content: {
                  type: "text",
                  text: `Error getting remote prompt: ${error.message}`
                }
              }]
            };
          }
        }
      );
    }
  }

  return server;
}

/**
 * Start MCP server with stdio transport (local mode)
 */
async function startStdioServer() {
  await ensureStorageDir();
  
  const server = await createMcpServer();
  const transport = new StdioServerTransport();
  
  await server.connect(transport);
  // Silently running in STDIO mode (logging would interfere with JSON-RPC)
}

/**
 * Start MCP server with StreamableHTTP transport (remote mode)
 */
async function startHttpServer() {
  await ensureStorageDir();
  
  const app = express();
  app.use(cors());
  app.use(express.json());

  // Health check
  app.get('/health', (req: Request, res: Response) => {
    res.json({ 
      status: 'ok',
      transport: 'streamable-http',
      serverName: 'Oncall Support MCP Core',
      version: '1.0.0'
    });
  });

  // Basic metrics (Prometheus text exposition format). Lightweight until full instrumentation.
  app.get('/metrics', (req: Request, res: Response) => {
    const memory = process.memoryUsage();
    const uptime = process.uptime();
    const toolCount = 10; // 7 JIRA tools + 3 support automation tools
    const lines = [
      '# HELP oncall_uptime_seconds Process uptime in seconds',
      '# TYPE oncall_uptime_seconds gauge',
      `oncall_uptime_seconds ${uptime.toFixed(0)}`,
      '# HELP oncall_memory_rss_bytes Resident set size in bytes',
      '# TYPE oncall_memory_rss_bytes gauge',
      `oncall_memory_rss_bytes ${memory.rss}`,
      '# HELP oncall_memory_heap_used_bytes Heap used in bytes',
      '# TYPE oncall_memory_heap_used_bytes gauge',
      `oncall_memory_heap_used_bytes ${memory.heapUsed}`,
      '# HELP oncall_tools_registered_count Number of MCP tools registered',
      '# TYPE oncall_tools_registered_count gauge',
      `oncall_tools_registered_count ${toolCount}`
    ];
    res.set('Content-Type', 'text/plain; version=0.0.4');
    res.send(lines.join('\n'));
  });

  // Info endpoint
  app.get('/', (req: Request, res: Response) => {
    res.json({
      name: 'Oncall Support MCP Core Server',
      version: '1.0.0',
      transport: 'StreamableHTTP',
      endpoints: {
        mcp: '/mcp',
        health: '/health'
      },
      usage: {
        inspector: `npx @modelcontextprotocol/inspector http://localhost:${HTTP_PORT}/mcp`,
        client: `Connect to http://localhost:${HTTP_PORT}/mcp`
      },
      note: 'For webhook integration, create a separate event processor service that connects as an MCP client'
    });
  });

  // MCP endpoint - stateless streamable HTTP
  // Handle ALL HTTP methods (GET for SSE, POST for messages, DELETE for session cleanup)
  app.all('/mcp', async (req: Request, res: Response) => {
    console.error(`📡 MCP ${req.method} request from:`, req.ip);
    
    try {
      // Create a new MCP server instance for this connection
      const server = await createMcpServer();
      
      // Create StreamableHTTP transport
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined // Stateless mode
      });
      
      // Handle connection close
      res.on('close', () => {
        console.error('🔌 MCP connection closed');
        transport.close();
        server.close();
      });
      
      // Connect server to transport
      await server.connect(transport);
      
      // Handle the HTTP request with parsed body
      await transport.handleRequest(req, res, req.body);
      
    } catch (error) {
      console.error('❌ Error handling MCP request:', error);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: {
            code: -32603,
            message: "Internal server error",
            data: error instanceof Error ? error.message : String(error)
          },
          id: null
        });
      }
    }
  });

  // Start the HTTP server
  app.listen(HTTP_PORT, () => {
    console.error("✅ MCP Core Server started in HTTP mode (remote)");
    console.error(`📍 HTTP Server: http://0.0.0.0:${HTTP_PORT}`);
    console.error(`🔧 MCP endpoint: http://0.0.0.0:${HTTP_PORT}/mcp`);
    console.error(`💚 Health check: http://0.0.0.0:${HTTP_PORT}/health`);
    console.error(`🔍 Test with: npx @modelcontextprotocol/inspector http://localhost:${HTTP_PORT}/mcp`);
    console.error(`📦 Transport: StreamableHTTP (stateless)`);
  });
}

/**
 * Main entry point - select transport based on CLI argument
 */
async function main() {
  const args = process.argv.slice(2);
  const transportArg = args.find(arg => arg.startsWith('--transport='));
  const portArg = args.find(arg => arg.startsWith('--port='));
  const transport = transportArg?.split('=')[1] || 'stdio';

  // Optional port override
  if (typeof portArg === 'string') {
    const eqIndex = portArg.indexOf('=');
    const valuePart: string = eqIndex >= 0 ? portArg.slice(eqIndex + 1) : '';
    const candidate = Number.parseInt(valuePart, 10);
    if (!Number.isNaN(candidate) && candidate > 0 && candidate < 65536) {
      HTTP_PORT = candidate;
      console.error(`🔧 Port override detected: using HTTP port ${HTTP_PORT}`);
    } else {
      console.error(`⚠️ Invalid --port value provided; continuing with ${HTTP_PORT}`);
    }
  }

  try {
    if (transport === 'dual' || transport === 'both') {
      // Start both HTTP and stdio servers simultaneously
      console.log('🚀 Starting MCP server in DUAL mode (HTTP + stdio)...\n');
      await Promise.all([
        startHttpServer(),
        startStdioServer()
      ]);
    } else if (transport === 'http' || transport === 'sse') {
      await startHttpServer();
    } else if (transport === 'stdio') {
      await startStdioServer();
    } else {
      console.error(`❌ Unknown transport: ${transport}`);
  console.error('Usage: node dist/mcp-server.js --transport=stdio|http|dual [--port=3001]');
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Error starting MCP server:", error);
    process.exit(1);
  }
}

main();
