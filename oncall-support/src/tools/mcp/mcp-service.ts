import fs from 'fs';
import path from 'path';
import axios from 'axios';

interface McpServerConfig { url: string; type: string; }
interface McpConfig { servers?: Record<string, McpServerConfig>; inputs?: any[]; }
interface McpTool { name: string; description?: string; schema?: any; }
interface McpPrompt { name: string; description?: string; }

const CACHE_DIR = path.join(process.cwd(), 'cache');
const TOOLS_CACHE_PATH = path.join(CACHE_DIR, 'mcp-tools.json');
const PROMPTS_CACHE_PATH = path.join(CACHE_DIR, 'mcp-prompts.json');

function ensureCacheDir() {
  if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR, { recursive: true });
}

function readMcpConfig(): McpConfig | null {
  const cfgPath = path.join(process.cwd(), 'mcp.json');
  if (!fs.existsSync(cfgPath)) return null;
  try { return JSON.parse(fs.readFileSync(cfgPath, 'utf8')); } catch { return null; }
}

function isMcpEnabled() {
  return process.env.ENABLE_MCP_SERVER === 'true';
}

export async function fetchMcpMetadata(forceRefresh = false) {
  if (!isMcpEnabled()) {
    return { tools: [], prompts: [], source: 'disabled' };
  }
  ensureCacheDir();
  if (!forceRefresh && fs.existsSync(TOOLS_CACHE_PATH) && fs.existsSync(PROMPTS_CACHE_PATH)) {
    try {
      const tools = JSON.parse(fs.readFileSync(TOOLS_CACHE_PATH, 'utf8')) as McpTool[];
      const prompts = JSON.parse(fs.readFileSync(PROMPTS_CACHE_PATH, 'utf8')) as McpPrompt[];
      return { tools, prompts, source: 'cache' };
    } catch {
      // fall through to refetch
    }
  }
  const cfg = readMcpConfig();
  const server = cfg?.servers?.['atlassian-mcp-server'];
  if (!server) {
    return { tools: [], prompts: [], source: 'missing-config' };
  }
  // NOTE: Atlassian MCP SSE would normally require EventSource; here we simulate metadata endpoints.
  try {
    // Placeholder endpoints; user may need to adjust based on actual MCP protocol
    const [toolsResp, promptsResp] = await Promise.all([
      axios.get(server.url.replace('/v1/sse', '/v1/tools')).catch(() => ({ data: [] })),
      axios.get(server.url.replace('/v1/sse', '/v1/prompts')).catch(() => ({ data: [] })),
    ]);
    const tools: McpTool[] = toolsResp.data || [];
    const prompts: McpPrompt[] = promptsResp.data || [];
    fs.writeFileSync(TOOLS_CACHE_PATH, JSON.stringify(tools, null, 2));
    fs.writeFileSync(PROMPTS_CACHE_PATH, JSON.stringify(prompts, null, 2));
    return { tools, prompts, source: 'remote' };
  } catch (err) {
    console.error('Failed to fetch MCP metadata:', err);
    return { tools: [], prompts: [], source: 'error' };
  }
}

export function listCachedMcpMetadata() {
  ensureCacheDir();
  let tools: McpTool[] = [];
  let prompts: McpPrompt[] = [];
  if (fs.existsSync(TOOLS_CACHE_PATH)) {
    try { tools = JSON.parse(fs.readFileSync(TOOLS_CACHE_PATH, 'utf8')); } catch {}
  }
  if (fs.existsSync(PROMPTS_CACHE_PATH)) {
    try { prompts = JSON.parse(fs.readFileSync(PROMPTS_CACHE_PATH, 'utf8')); } catch {}
  }
  return { tools, prompts };
}

export function formatMetadataForDisplay(tools: McpTool[], prompts: McpPrompt[]) {
  const toolLines = tools.map(t => `• ${t.name}${t.description ? ' - ' + t.description : ''}`);
  const promptLines = prompts.map(p => `• ${p.name}${p.description ? ' - ' + p.description : ''}`);
  return `MCP Tools (count: ${tools.length})\n${toolLines.join('\n') || 'None'}\n\nMCP Prompts (count: ${prompts.length})\n${promptLines.join('\n') || 'None'}`;
}

export async function getMcpOverview(forceRefresh = false) {
  const { tools, prompts, source } = await fetchMcpMetadata(forceRefresh);
  return formatMetadataForDisplay(tools, prompts) + `\n\nSource: ${source}`;
}
