import { z } from 'zod';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';

// ---------------- Configuration Helpers ----------------
function getJiraConfig() {
  const JIRA_BASE_URL = process.env.JIRA_BASE_URL || '';
  const JIRA_USERNAME = process.env.JIRA_USERNAME || '';
  const JIRA_API_TOKEN = process.env.JIRA_API_TOKEN || '';
  if (!JIRA_BASE_URL || !JIRA_USERNAME || !JIRA_API_TOKEN) {
    const missing: string[] = [];
    if (!JIRA_BASE_URL) missing.push('JIRA_BASE_URL');
    if (!JIRA_USERNAME) missing.push('JIRA_USERNAME');
    if (!JIRA_API_TOKEN) missing.push('JIRA_API_TOKEN');
    throw new Error(`Missing Jira credentials: ${missing.join(', ')}`);
  }
  return { JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN };
}

function readMcpConfig() {
  const workspaceDir = process.cwd();
  const homeDir = process.env.HOME || process.env.USERPROFILE || '';
  const paths = [path.join(workspaceDir, 'mcp.json')];
  if (homeDir) paths.push(path.join(homeDir, 'mcp.json'));
  for (const p of paths) {
    if (fs.existsSync(p)) {
      try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { /* ignore */ }
    }
  }
  return null;
}

// ---------------- HTTP Helpers ----------------
export async function makeJiraRequest(endpoint: string) {
  const mcp = readMcpConfig();
  if (mcp?.servers?.['atlassian-mcp-server']) {
    try {
      const server = mcp.servers['atlassian-mcp-server'];
      const resp = await axios.post(server.url, { endpoint, method: 'GET' });
      return resp.data;
    } catch (err) {
      console.error('MCP call (GET) failed, falling back:', err);
    }
  }
  const { JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN } = getJiraConfig();
  const url = `${JIRA_BASE_URL}/rest/api/3/${endpoint}`;
  const auth = Buffer.from(`${JIRA_USERNAME}:${JIRA_API_TOKEN}`).toString('base64');
  const resp = await axios.get(url, { headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' } });
  return resp.data;
}

export async function makeJiraWriteRequest(method: 'POST' | 'PUT' | 'DELETE', endpoint: string, data?: any) {
  const mcp = readMcpConfig();
  if (mcp?.servers?.['atlassian-mcp-server']) {
    try {
      const server = mcp.servers['atlassian-mcp-server'];
      const resp = await axios.post(server.url, { endpoint, method, data });
      return resp.data;
    } catch (err) {
      console.error('MCP call (write) failed, falling back:', err);
    }
  }
  const { JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN } = getJiraConfig();
  const url = `${JIRA_BASE_URL}/rest/api/3/${endpoint}`;
  const auth = Buffer.from(`${JIRA_USERNAME}:${JIRA_API_TOKEN}`).toString('base64');
  const resp = await axios({ method, url, headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' }, data });
  return resp.data;
}

// ---------------- Data Shapes ----------------
interface RawTicket { key: string; fields: any; changelog?: any; }
interface CompactTicket {
  key: string; summary: string; status: string; priority: string; issueType: string;
  assignee: string; reporter: string; created: string; updated: string; labels: string[]; components: string[];
  descriptionExcerpt?: string; commentsExcerpt?: Array<{ a: string; c: string; t: string }>; changelogExcerpt?: Array<{ t: string; a: string; f: string; from?: string; to?: string }>; }

function envNum(name: string, def: number) { const raw = process.env[name]; const n = raw ? parseInt(raw, 10) : NaN; return Number.isFinite(n) && n > 0 ? n : def; }
const MAX_DESCRIPTION_CHARS = envNum('JIRA_COMPACT_MAX_DESCRIPTION_CHARS', 600);
const MAX_COMMENT_COUNT = envNum('JIRA_COMPACT_MAX_COMMENT_COUNT', 5);
const MAX_COMMENT_CHARS = envNum('JIRA_COMPACT_MAX_COMMENT_CHARS', 220);
const MAX_CHANGELOG_ITEMS = envNum('JIRA_COMPACT_MAX_CHANGELOG_ITEMS', 8);
const ENABLE_COMPACT_DEFAULT = process.env.ENABLE_JIRA_COMPACT === 'true';

function truncate(str: string, max: number) { return str && str.length > max ? str.slice(0, max) + '…' : str; }
function extractTextFromADF(adf: any): string {
  if (!adf) return ''; if (typeof adf === 'string') return adf; let out = '';
  const walk = (node: any) => { if (!node) return; if (node.type === 'text' && node.text) out += node.text + ' '; if (Array.isArray(node.content)) node.content.forEach(walk); };
  walk(adf); return out.trim();
}

export async function fetchRawTicket(ticketId: string): Promise<RawTicket> { return makeJiraRequest(`issue/${ticketId}?expand=changelog`); }

export function toCompactTicket(raw: RawTicket): CompactTicket {
  const f = raw.fields; const comments: any[] = f.comment?.comments || []; const histories: any[] = raw.changelog?.histories || [];
  let desc = ''; if (typeof f.description === 'string') desc = f.description; else if (f.description) desc = extractTextFromADF(f.description);
  return {
    key: raw.key,
    summary: f.summary,
    status: f.status?.name || 'Unknown',
    priority: f.priority?.name || 'Not set',
    issueType: f.issuetype?.name || 'Unknown',
    assignee: f.assignee?.displayName || 'Unassigned',
    reporter: f.reporter?.displayName || 'Unknown',
    created: f.created,
    updated: f.updated,
    labels: f.labels || [],
    components: (f.components || []).map((c: any) => c.name),
    descriptionExcerpt: truncate(desc, MAX_DESCRIPTION_CHARS),
    commentsExcerpt: comments.slice(0, MAX_COMMENT_COUNT).map(c => ({ a: c.author.displayName, t: c.created, c: truncate(typeof c.body === 'string' ? c.body : extractTextFromADF(c.body), MAX_COMMENT_CHARS) })),
    changelogExcerpt: histories.slice(0, MAX_CHANGELOG_ITEMS).flatMap(h => h.items.map((item: any) => ({ t: h.created, a: h.author.displayName, f: item.field, from: item.fromString || undefined, to: item.toString || undefined }))).slice(0, MAX_CHANGELOG_ITEMS)
  };
}

function compactTicketMarkdown(ct: CompactTicket) {
  const comments = ct.commentsExcerpt && ct.commentsExcerpt.length ? ct.commentsExcerpt.map((c,i)=>`${i+1}. ${c.a} (${c.t}): ${c.c}`).join('\n') : 'None';
  const changes = ct.changelogExcerpt && ct.changelogExcerpt.length ? ct.changelogExcerpt.map(ch=>`${ch.t} ${ch.a} ${ch.f}: ${ch.from||'∅'} → ${ch.to||'∅'}`).join('\n') : 'None';
  return `# Jira Ticket: ${ct.key}\nSummary: ${ct.summary}\nStatus: ${ct.status} | Priority: ${ct.priority} | Type: ${ct.issueType}\nAssignee: ${ct.assignee} | Reporter: ${ct.reporter}\nCreated: ${ct.created} | Updated: ${ct.updated}\nLabels: ${ct.labels.join(', ')||'None'} | Components: ${ct.components.join(', ')||'None'}\n\nDescription (truncated):\n${ct.descriptionExcerpt||'No description'}\n\nComments (up to ${MAX_COMMENT_COUNT}):\n${comments}\n\nChangelog (sample):\n${changes}`;
}

// ---------------- Tools ----------------
export const getJiraTicket = {
  name: 'get-jira-ticket',
  description: 'Retrieve Jira ticket details (compact mode optional).',
  schema: { ticketId: z.string().describe('Ticket key (e.g. PROJ-123)'), compact: z.boolean().optional() },
  handler: async ({ ticketId, compact }: { ticketId: string; compact?: boolean }) => {
    try {
      const raw = await fetchRawTicket(ticketId);
      const useCompact = typeof compact === 'boolean' ? compact : ENABLE_COMPACT_DEFAULT;
      const ct = toCompactTicket(raw);
      return { content: [{ type: 'text' as const, text: compactTicketMarkdown(ct) }] };
    } catch (err) {
      return { content: [{ type: 'text' as const, text: `Error fetching ${ticketId}: ${err instanceof Error ? err.message : String(err)}` }], isError: true };
    }
  }
};

export const searchJiraTickets = {
  name: 'search-jira-tickets',
  description: 'Run JQL search with optional compact summary list.',
  schema: { jql: z.string(), maxResults: z.number().optional().default(10), compact: z.boolean().optional() },
  handler: async ({ jql, maxResults, compact }: { jql: string; maxResults?: number; compact?: boolean }) => {
    try {
      const max = maxResults || 10;
      const data = await makeJiraRequest(`search?jql=${encodeURIComponent(jql)}&maxResults=${max}&fields=key,summary,status,priority,assignee,created,updated`);
      const issues: any[] = data.issues || [];
      const rows = issues.map(i => ({ k: i.key, s: i.fields.summary, st: i.fields.status?.name || 'Unknown', p: i.fields.priority?.name || 'Not set', a: i.fields.assignee?.displayName || 'Unassigned', u: i.fields.updated }));
      const useCompact = typeof compact === 'boolean' ? compact : ENABLE_COMPACT_DEFAULT;
      if (useCompact) {
        return { content: [{ type: 'text' as const, text: `# Jira Search (Compact)\nCount: ${rows.length}\n` + rows.map(r => `${r.k} | ${truncate(r.s,120)} | ${r.st} | ${r.p} | ${r.a}`).join('\n') }] };
      }
      return { content: [{ type: 'text' as const, text: `Jira Search Results (${rows.length})\n\n` + rows.map((r,i)=>`${i+1}. ${r.k}: ${r.s}\n   Status: ${r.st} | Priority: ${r.p} | Assignee: ${r.a}\n   Updated: ${r.u}`).join('\n\n') }] };
    } catch (err) {
      return { content: [{ type: 'text' as const, text: `Error executing JQL: ${err instanceof Error ? err.message : String(err)}` }], isError: true };
    }
  }
};

export const addJiraComment = {
  name: 'add-jira-comment',
  description: 'Add a comment to a Jira ticket (ADF paragraphs per newline).',
  schema: { ticketId: z.string(), body: z.string(), visibility: z.object({ type: z.enum(['role','group']), value: z.string() }).optional() },
  handler: async ({ ticketId, body, visibility }: { ticketId: string; body: string; visibility?: { type: 'role'|'group'; value: string } }) => {
    try {
      const content = body.split('\n').filter(l=>l.trim()).map(line => ({ type: 'paragraph', content: [{ type: 'text', text: line }] }));
      const payload: any = { body: { type: 'doc', version: 1, content } }; if (visibility) payload.visibility = visibility;
      await makeJiraWriteRequest('POST', `issue/${ticketId}/comment`, payload);
      return { content: [{ type: 'text' as const, text: `✅ Comment added to ${ticketId}` }] };
    } catch (err) { return { content: [{ type: 'text' as const, text: `❌ Error adding comment: ${err instanceof Error ? err.message : String(err)}` }], isError: true }; }
  }
};

export const updateJiraFields = {
  name: 'update-jira-fields',
  description: 'Update priority, labels, components, and custom fields.',
  schema: { ticketId: z.string(), updates: z.object({ priority: z.object({ name: z.string() }).optional(), labels: z.array(z.string()).optional(), components: z.array(z.object({ name: z.string() })).optional(), customFields: z.record(z.any()).optional() }) },
  handler: async ({ ticketId, updates }: { ticketId: string; updates: any }) => {
    try {
      const payload: any = { fields: {} };
      if (updates.priority) payload.fields.priority = updates.priority;
      if (updates.labels) payload.fields.labels = updates.labels;
      if (updates.components) payload.fields.components = updates.components;
      if (updates.customFields) Object.assign(payload.fields, updates.customFields);
      await makeJiraWriteRequest('PUT', `issue/${ticketId}`, payload);
      return { content: [{ type: 'text' as const, text: `✅ Updated ${ticketId}` }] };
    } catch (err) { return { content: [{ type: 'text' as const, text: `❌ Field update failed: ${err instanceof Error ? err.message : String(err)}` }], isError: true }; }
  }
};

export const transitionJiraTicket = {
  name: 'transition-jira-ticket',
  description: 'Perform a workflow transition; optional comment.',
  schema: { ticketId: z.string(), transitionId: z.string(), comment: z.string().optional() },
  handler: async ({ ticketId, transitionId, comment }: { ticketId: string; transitionId: string; comment?: string }) => {
    try {
      const payload: any = { transition: { id: transitionId } };
      if (comment) {
        payload.update = { comment: [{ add: { body: { type: 'doc', version: 1, content: [{ type: 'paragraph', content: [{ type: 'text', text: comment }] }] } } }] };
      }
      await makeJiraWriteRequest('POST', `issue/${ticketId}/transitions`, payload);
      return { content: [{ type: 'text' as const, text: `✅ Transitioned ${ticketId}` }] };
    } catch (err) { return { content: [{ type: 'text' as const, text: `❌ Transition failed: ${err instanceof Error ? err.message : String(err)}` }], isError: true }; }
  }
};

export const getJiraTransitions = {
  name: 'get-jira-transitions',
  description: 'List available workflow transitions for a ticket.',
  schema: { ticketId: z.string() },
  handler: async ({ ticketId }: { ticketId: string }) => {
    try {
      const data = await makeJiraRequest(`issue/${ticketId}/transitions`);
      const transitions: any[] = data.transitions || [];
      const lines = transitions.map(t => `ID: ${t.id} | Name: ${t.name} | To: ${t.to?.name || 'Unknown'}`).join('\n');
      return { content: [{ type: 'text' as const, text: `# Transitions for ${ticketId}\n${lines || 'None'}` }] };
    } catch (err) { return { content: [{ type: 'text' as const, text: `❌ Error listing transitions: ${err instanceof Error ? err.message : String(err)}` }], isError: true }; }
  }
};

export const getJiraFieldOptions = {
  name: 'get-jira-field-options',
  description: 'Fetch allowed values for a custom field (editmeta fallback).',
  schema: { fieldKey: z.string(), ticketId: z.string().optional() },
  handler: async ({ fieldKey, ticketId }: { fieldKey: string; ticketId?: string }) => {
    try {
      const endpoint = ticketId ? `issue/${ticketId}/editmeta` : `field/${fieldKey}/option`;
      const data = await makeJiraRequest(endpoint);
      let options: any[] = [];
      if (data.values) options = data.values; else if (data.fields?.[fieldKey]?.allowedValues) options = data.fields[fieldKey].allowedValues;
      const text = options.map(o => {
        const base = `Value: "${o.value}"${o.id ? ` (ID: ${o.id})` : ''}`;
        if (o.cascadingOptions) return base + '\n' + o.cascadingOptions.map((c: any) => `  - ${c.value}`).join('\n');
        return base;
      }).join('\n\n');
      return { content: [{ type: 'text' as const, text: `# Field Options: ${fieldKey}\n${text || 'No options'}` }] };
    } catch (err) { return { content: [{ type: 'text' as const, text: `❌ Error fetching field options: ${err instanceof Error ? err.message : String(err)}` }], isError: true }; }
  }
};

// ---------------- Aggregated Service Export ----------------
export const jiraService = {
  getTicket: getJiraTicket,
  searchTickets: searchJiraTickets,
  addComment: addJiraComment,
  updateFields: updateJiraFields,
  transitionTicket: transitionJiraTicket,
  getTransitions: getJiraTransitions,
  getFieldOptions: getJiraFieldOptions,
  fetchRawTicket,
  toCompactTicket
};

// Backwards compatible individual exports
export const getJiraTicketTool = getJiraTicket;
export const searchJiraTicketsTool = searchJiraTickets;
export const addJiraCommentTool = addJiraComment;
export const updateJiraFieldsTool = updateJiraFields;
export const transitionJiraTicketTool = transitionJiraTicket;
export const getJiraTransitionsTool = getJiraTransitions;
export const getJiraFieldOptionsTool = getJiraFieldOptions;
