import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import fs from 'fs';
import path from 'path';

interface McpServerConfig {
  url: string;
  type: string;
}

interface McpConfig {
  servers?: Record<string, McpServerConfig>;
  inputs?: any[];
}

interface RemoteTool {
  name: string;
  description?: string;
  inputSchema: any;
}

interface RemotePrompt {
  name: string;
  description?: string;
  arguments?: any[];
}

let mcpClient: Client | null = null;
let remoteTools: RemoteTool[] = [];
let remotePrompts: RemotePrompt[] = [];
let connectionError: string | null = null;

function readMcpConfig(): McpConfig | null {
  const cfgPath = path.join(process.cwd(), 'mcp.json');
  if (!fs.existsSync(cfgPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  } catch {
    return null;
  }
}

function isMcpEnabled(): boolean {
  return process.env.ENABLE_MCP_SERVER === 'true';
}

/**
 * Connect to remote MCP server and fetch available tools and prompts
 */
export async function connectToRemoteMcpServer(): Promise<void> {
  if (!isMcpEnabled()) {
    return;
  }

  const cfg = readMcpConfig();
  const server = cfg?.servers?.['atlassian-mcp-server'];
  
  if (!server) {
    return;
  }

  try {
    // Create SSE transport for the remote server
    const transport = new SSEClientTransport(new URL(server.url));
    
    // Create MCP client
    mcpClient = new Client({
      name: 'oncall-support-mcp-client',
      version: '1.0.0'
    }, {
      capabilities: {}
    });

    // Connect to the remote server
    await mcpClient.connect(transport);

    // Fetch available tools
    const toolsResponse = await mcpClient.listTools();
    remoteTools = toolsResponse.tools || [];

    // Fetch available prompts
    const promptsResponse = await mcpClient.listPrompts();
    remotePrompts = promptsResponse.prompts || [];

    connectionError = null;
  } catch (error: any) {
    connectionError = error.message || 'Unknown error';
    // Log error to a file for debugging (not to console)
    mcpClient = null;
    remoteTools = [];
    remotePrompts = [];
  }
}

/**
 * Get list of remote tools
 */
export function getRemoteTools(): RemoteTool[] {
  return remoteTools;
}

/**
 * Get list of remote prompts
 */
export function getRemotePrompts(): RemotePrompt[] {
  return remotePrompts;
}

/**
 * Call a remote tool by name
 */
export async function callRemoteTool(toolName: string, args: any): Promise<any> {
  if (!mcpClient) {
    throw new Error('MCP client not connected');
  }

  try {
    const response = await mcpClient.callTool({
      name: toolName,
      arguments: args
    });
    
    return response;
  } catch (error: any) {
    throw new Error(`Failed to call remote tool ${toolName}: ${error.message}`);
  }
}

/**
 * Get a remote prompt by name
 */
export async function getRemotePrompt(promptName: string, args: any): Promise<any> {
  if (!mcpClient) {
    throw new Error('MCP client not connected');
  }

  try {
    const response = await mcpClient.getPrompt({
      name: promptName,
      arguments: args
    });
    
    return response;
  } catch (error: any) {
    throw new Error(`Failed to get remote prompt ${promptName}: ${error.message}`);
  }
}

/**
 * Get connection status
 */
export function getConnectionStatus(): {
  connected: boolean;
  toolCount: number;
  promptCount: number;
  error: string | null;
} {
  return {
    connected: mcpClient !== null,
    toolCount: remoteTools.length,
    promptCount: remotePrompts.length,
    error: connectionError
  };
}

/**
 * Disconnect from remote MCP server
 */
export async function disconnectFromRemoteMcpServer(): Promise<void> {
  if (mcpClient) {
    try {
      await mcpClient.close();
    } catch (error) {
      // Silent error
    }
    mcpClient = null;
    remoteTools = [];
    remotePrompts = [];
  }
}
